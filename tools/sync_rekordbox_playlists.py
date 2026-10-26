#!/usr/bin/env python3
"""Mirror Dan's hand-made rekordbox playlists into the Music app.

rekordbox is the source. Every normal playlist/folder in rekordbox's own tree (not the iTunes tree)
is recreated under the top-level Music folder ROOT ("11 rekordbox"), same nesting, same track order.
Re-running updates Music: renames, moves, track changes, and deletes mirrors of playlists that were
removed in rekordbox. Only playlists this script created (tracked in STATE) are ever touched.

Reads a COPY of master.db, so rekordbox may stay open. Tracks are matched by file path.

Run (pyrekordbox venv):
    ~/rekordbox-automation/venv/bin/python tools/sync_rekordbox_playlists.py            # sync
    ~/rekordbox-automation/venv/bin/python tools/sync_rekordbox_playlists.py --dry-run  # show plan only
Built by Hermes.
"""
import argparse, json, os, re, shutil, subprocess, sys, unicodedata, urllib.parse, warnings

warnings.filterwarnings("ignore")
import logging
logging.disable(logging.WARNING)
from pyrekordbox import Rekordbox6Database

ROOT = "11 rekordbox"
MASTER = os.path.expanduser("~/Library/Pioneer/rekordbox/master.db")
COPY = "/tmp/rb_playlist_sync.db"
STATE = os.path.expanduser("~/rekordbox-automation/rb_music_playlists.json")
EXCLUDE = [r"^CUE Analysis Playlist", r"^Analyze LOCK$"]   # rekordbox utility lists, not real playlists


def norm(p):
    return unicodedata.normalize("NFC", p).lower()


def osa(script, *args):
    r = subprocess.run(["osascript", "-", *args], input=script, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


# ---------- rekordbox side ----------
def read_rekordbox():
    for ext in ("", "-wal", "-shm"):
        if os.path.exists(MASTER + ext):
            shutil.copy(MASTER + ext, COPY + ext)
        elif os.path.exists(COPY + ext):
            os.remove(COPY + ext)
    db = Rekordbox6Database(path=COPY)
    pls = {p.ID: p for p in db.get_playlist().all()}
    nodes = {}
    for p in pls.values():
        if any(re.search(x, p.Name or "") for x in EXCLUDE):
            continue
        if p.Attribute not in (0, 1, 4):   # 0 playlist, 1 folder, 4 intelligent (mirrored as a static copy)
            continue
        songs = []
        if p.Attribute != 1:
            if p.Attribute == 4:
                songs = [c.FolderPath for c in db.get_playlist_contents(p)]
            else:
                rows = sorted(db.get_playlist_songs(PlaylistID=p.ID).all(), key=lambda s: s.TrackNo or 0)
                songs = [s.Content.FolderPath for s in rows if s.Content]
        nodes[str(p.ID)] = {"name": p.Name, "folder": p.Attribute == 1,
                            "parent": str(p.ParentID) if p.ParentID and p.ParentID != "root" else None,
                            "seq": p.Seq or 0, "paths": songs}
    # drop children of excluded/unknown parents -> attach to root
    for n in nodes.values():
        if n["parent"] not in nodes:
            n["parent"] = None
    db.close()
    return nodes


# ---------- Music side ----------
def music_tracks():
    js = ('var l=Application("Music").libraryPlaylists[0].fileTracks;'
          'var a=l.location(),b=l.persistentID(),o=[];'
          'for(var i=0;i<a.length;i++){if(a[i])o.push([String(a[i]),b[i]])}JSON.stringify(o)')
    r = subprocess.run(["osascript", "-l", "JavaScript", "-e", js], capture_output=True, text=True, check=True)
    return {norm(path): pid for path, pid in json.loads(r.stdout)}


AS_FIND = '''
on run argv
  tell application "Music"
    set pidList to {}
    try
      set p to (first playlist whose persistent ID is (item 1 of argv))
      set k to "user"
      if class of p is folder playlist then set k to "folder"
      set pn to ""
      try
        set pn to persistent ID of parent of p
      end try
      return k & tab & (name of p) & tab & pn
    on error
      return "missing"
    end try
  end tell
end run'''

AS_CREATE = '''
on run argv
  set {theKind, theName, thePid} to argv
  tell application "Music"
    if theKind is "folder" then
      if thePid is "" then
        set p to make new folder playlist with properties {name:theName}
      else
        set p to make new folder playlist at (first playlist whose persistent ID is thePid) with properties {name:theName}
      end if
    else
      if thePid is "" then
        set p to make new user playlist with properties {name:theName}
      else
        set p to make new user playlist at (first playlist whose persistent ID is thePid) with properties {name:theName}
      end if
    end if
    return persistent ID of p
  end tell
end run'''

AS_FIX = '''
on run argv
  set {thePl, theName, thePid} to argv
  tell application "Music"
    set p to (first playlist whose persistent ID is thePl)
    if name of p is not theName then set name of p to theName
    set cur to ""
    try
      set cur to persistent ID of parent of p
    end try
    if cur is not thePid then move p to (first playlist whose persistent ID is thePid)
  end tell
end run'''

AS_TRACKS = '''
on run argv
  tell application "Music"
    set p to (first playlist whose persistent ID is (item 1 of argv))
    try
      set ids to persistent ID of every track of p
    on error
      set ids to {}
    end try
  end tell
  set AppleScript's text item delimiters to linefeed
  return ids as text
end run'''

AS_SET = '''
on run argv
  tell application "Music"
    set p to (first playlist whose persistent ID is (item 1 of argv))
    delete every track of p
    set lib to library playlist 1
    repeat with i from 2 to count of argv
      try
        duplicate (first track of lib whose persistent ID is (item i of argv)) to p
      end try
    end repeat
    return count of tracks of p
  end tell
end run'''

AS_DELETE = '''
on run argv
  tell application "Music"
    try
      delete (first playlist whose persistent ID is (item 1 of argv))
    end try
  end tell
end run'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    nodes = read_rekordbox()
    tracks = music_tracks()
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    dry = a.dry_run

    def find(pid):
        if not pid:
            return None
        r = osa(AS_FIND, pid)
        return None if r == "missing" else r.split("\t")

    # root folder
    root = state.get("__root__")
    if not find(root):
        root = None if dry else osa(AS_CREATE, "folder", ROOT, "")
        print(f"create folder {ROOT}")
    state["__root__"] = root

    def depth(i):
        d, n = 0, nodes[i]
        while n["parent"]:
            d, n = d + 1, nodes[n["parent"]]
        return d

    def fullname(i):
        n, parts = nodes[i], []
        while True:
            parts.append(n["name"])
            if not n["parent"]:
                break
            n = nodes[n["parent"]]
        return " > ".join(reversed(parts))

    unmatched, changed = {}, 0
    for i in sorted(nodes, key=lambda i: (depth(i), nodes[i]["seq"])):
        n = nodes[i]
        kind = "folder" if n["folder"] else "user"
        parent_pid = state.get(n["parent"]) if n["parent"] else root
        pid = state.get(i)
        info = find(pid)
        if info and info[0] != kind:      # folder <-> playlist changed in rekordbox: recreate
            if not dry:
                osa(AS_DELETE, pid)
            info = None
        if not info:
            print(f"create {kind:6} {fullname(i)}")
            pid = None if dry else osa(AS_CREATE, kind, n["name"], parent_pid or "")
            state[i] = pid
            changed += 1
        elif info[1] != n["name"] or info[2] != (parent_pid or ""):
            print(f"rename/move     {fullname(i)}")
            if not dry:
                osa(AS_FIX, pid, n["name"], parent_pid or "")
            changed += 1
        if n["folder"]:
            continue
        want = []
        for p in n["paths"]:
            mp = tracks.get(norm(p))
            if mp:
                want.append(mp)
            else:
                unmatched.setdefault(fullname(i), []).append(p)
        have = osa(AS_TRACKS, pid).splitlines() if pid and not dry else []
        if have != want:
            print(f"tracks {len(have):4} -> {len(want):4}  {fullname(i)}")
            if not dry:
                got = int(osa(AS_SET, pid, *want))
                if got != len(want):
                    print(f"  WARNING: Music has {got}, expected {len(want)}")
            changed += 1

    # rekordbox playlists that were deleted -> delete their mirror
    for i in [k for k in state if k != "__root__" and k not in nodes]:
        print(f"delete mirror of removed rekordbox playlist (id {i})")
        if not dry and state[i]:
            osa(AS_DELETE, state[i])
        state.pop(i)
        changed += 1

    if not dry:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        json.dump(state, open(STATE, "w"), indent=1)
    for k, v in unmatched.items():
        print(f"not in Music ({len(v)}): {k}")
        for p in v[:5]:
            print("   ", p)
    print(f"{'DRY RUN: ' if dry else ''}{len(nodes)} rekordbox playlists/folders, {changed} changes")


if __name__ == "__main__":
    main()
