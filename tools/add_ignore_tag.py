#!/usr/bin/env python3
"""Add an Ignore tag to every track of a Music playlist (default "Add ignore").

New comment: empty -> "Ignore"; "KEY - E" -> "KEY - E - Ignore"; "KEY - E - tags" -> "KEY - E - tags, Ignore".
Tracks already containing "ignore" are skipped. Backs up persistent ID/artist/name/old comment to
~/Documents/MIK-backup-YYYYMMDD/add-ignore-<time>.tsv first. Writes via Music (which updates the file tag).
Usage: python3 tools/add_ignore_tag.py [--playlist NAME] [--limit N] [--dry-run]
Built by Hermes.
"""
import argparse, datetime, json, os, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--playlist", default="Add ignore")
ap.add_argument("--limit", type=int)
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

js = f'''var p=Application("Music").userPlaylists.whose({{name:{json.dumps(a.playlist)}}})()[0];var t=p.tracks;
t.length?JSON.stringify([t.persistentID(),t.artist(),t.name(),t.comment()]):"[[],[],[],[]]"'''
ids, artists, names, comments = json.loads(subprocess.run(["osascript", "-l", "JavaScript", "-e", js],
                                                          capture_output=True, text=True, check=True).stdout)


def new_comment(c):
    s = (c or "").strip()
    if not s:
        return "Ignore"
    if re.fullmatch(r"[\d/AB]*\s*- \d+", s):
        return s + " - Ignore"
    return s + ", Ignore"


todo = [(i, ar, n, c, new_comment(c)) for i, ar, n, c in zip(ids, artists, names, comments)
        if "ignore" not in (c or "").lower()]
if a.limit:
    todo = todo[:a.limit]
print(f"{len(ids)} tracks in '{a.playlist}', {len(todo)} to change")
for row in todo[:5]:
    print(f"  {row[3]!r} -> {row[4]!r}  | {row[1]} - {row[2]}")
if a.dry_run or not todo:
    raise SystemExit

d = os.path.expanduser(f"~/Documents/MIK-backup-{datetime.date.today():%Y%m%d}")
os.makedirs(d, exist_ok=True)
bk = os.path.join(d, f"add-ignore-{datetime.datetime.now():%H%M%S}.tsv")
with open(bk, "w") as f:
    for i, ar, n, c, _ in todo:
        f.write("\t".join([i, ar or "", n or "", json.dumps(c or "")]) + "\n")
print("backup:", bk)

AS = '''on run argv
  tell application "Music"
    set lib to library playlist 1
    set bad to 0
    repeat with i from 1 to (count of argv) by 2
      try
        set t to (first track of lib whose persistent ID is (item i of argv))
        set comment of t to (item (i + 1) of argv)
      on error
        set bad to bad + 1
      end try
    end repeat
    return bad
  end tell
end run'''
args = [x for row in todo for x in (row[0], row[4])]
r = subprocess.run(["osascript", "-", *args], input=AS, capture_output=True, text=True)
print("errors:", r.stdout.strip() or r.stderr.strip())

# verify
want = {row[0]: row[4] for row in todo}
js2 = 'var l=Application("Music").libraryPlaylists[0].tracks;JSON.stringify([l.persistentID(),l.comment()])'
pi, pc = json.loads(subprocess.run(["osascript", "-l", "JavaScript", "-e", js2], capture_output=True, text=True).stdout)
got = dict(zip(pi, pc))
ok = sum(1 for k, v in want.items() if (got.get(k) or "").strip() == v)
print(f"verified {ok}/{len(want)}")
