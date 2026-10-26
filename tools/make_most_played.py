#!/usr/bin/env python3
"""Music playlist "Most Played (rekordbox)": Dan's most played tracks according to rekordbox.

Ranks rekordbox tracks by DJ play count (ties: number of history sessions), takes the top N
(default 100), and fills a top-level static Music playlist in that order (most played first).
Reads a COPY of master.db, so rekordbox can stay open; the playlist also shows in rekordbox's
iTunes tree. Rerun to refresh (the playlist is updated in place, so its view is kept).

Run: ~/rekordbox-automation/venv/bin/python tools/make_most_played.py [--top N] [--dry-run]
Built by Hermes.
"""
import argparse, collections, json, os, shutil, subprocess, sys, unicodedata, warnings, logging
warnings.filterwarnings("ignore"); logging.disable(logging.WARNING)
from pyrekordbox import Rekordbox6Database
from pyrekordbox.db6 import tables
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_rekordbox_playlists import music_tracks, norm, osa, AS_TRACKS, AS_SET

NAME = "Most Played (rekordbox)"
MASTER = os.path.expanduser("~/Library/Pioneer/rekordbox/master.db")
COPY = "/tmp/rb_most_played.db"


def ranking():
    for e in ("", "-wal", "-shm"):
        if os.path.exists(MASTER + e):
            shutil.copy(MASTER + e, COPY + e)
    db = Rekordbox6Database(path=COPY)
    sessions = collections.defaultdict(set)
    for s in db.query(tables.DjmdSongHistory).all():
        sessions[s.ContentID].add(s.HistoryID)
    rows = [(int(c.DJPlayCount or 0), len(sessions[c.ID]), c.FolderPath, c.ArtistName, c.Title)
            for c in db.get_content().all() if c.DJPlayCount]
    db.close()
    return sorted(rows, key=lambda r: (-r[0], -r[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=100)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tracks = music_tracks()
    want, missing = [], []
    for plays, sess, path, artist, title in ranking():
        if len(want) >= a.top:
            break
        pid = tracks.get(norm(path or ""))
        (want.append((pid, plays, artist, title)) if pid else missing.append((plays, artist, title)))
    for i, (_, plays, artist, title) in enumerate(want[:10], 1):
        print(f"{i:3}. {plays:3} plays  {artist} - {title}")
    print(f"... {len(want)} tracks, plays {want[-1][1]}-{want[0][1]}; skipped (not in Music): {len(missing)}")
    for m in missing:
        print("   not in Music:", m)
    if a.dry_run:
        return
    pl = osa('tell application "Music"\nif not (exists user playlist "%s") then make new user playlist with properties {name:"%s"}\n'
             'return persistent ID of user playlist "%s"\nend tell' % (NAME, NAME, NAME))
    ids = [w[0] for w in want]
    if osa(AS_TRACKS, pl).splitlines() == ids:
        print("unchanged")
        return
    got = int(osa(AS_SET, pl, *ids))
    print(f"'{NAME}' now has {got} tracks" + ("" if got == len(ids) else f" (expected {len(ids)})"))


if __name__ == "__main__":
    main()
