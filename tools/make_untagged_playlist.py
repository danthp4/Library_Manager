#!/usr/bin/env python3
"""Build a top-level Music smart playlist "To Tag": every music track that still needs tagging.

Rule: media kind music AND comment has none of the Genre.xlsx tags as a whole word (", T," / "- T," /
ends ", T" / ends "- T") AND comment does not contain Ignore or Archive. So it holds unanalysed tracks
(empty / non-MIK comments), analysed-but-untagged ones ("8A - 7" or "8A - 7 - <junk/url>") and comments
with only typo/cut-off tags. Tagged and Ignore/Archive tracks are excluded.

Usage (from Library_Manager): venv/bin/python tools/make_untagged_playlist.py [--check] [--no-import]
  --check  only compute the expected set from Music comments and print a breakdown.
Rerun after editing Genre.xlsx (it replaces the playlist; reapply the view afterwards).
Built by Hermes.
"""
import copy, datetime, json, os, plistlib, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import openpyxl
from make_tag_playlists import (XLSX, TEMPLATE, SMART_INFO, EXTRA_SPELLINGS, parse, enc, rule, pid)

NAME = "To Tag"
OUT = "/tmp/music_to_tag.xml"
NOT_CONTAINS, NOT_ENDS = 0x03000002, 0x03000008
EXCLUDE_WORDS = ["Ignore", "Archive"]


def tags():
    rows = list(openpyxl.load_workbook(XLSX).worksheets[0].iter_rows(values_only=True))
    cols = [str(c).lstrip("\ufeff").strip() for c in rows[0]]
    out = []
    for i, col in enumerate(cols):
        if col == "Ignore":
            continue
        for r in rows[1:]:
            if i < len(r) and r[i]:
                out += EXTRA_SPELLINGS.get(str(r[i]).strip(), [str(r[i]).strip()])
    return out


def is_untagged(comment, tag_list):
    c = (comment or "").lower()
    if any(w.lower() in c for w in EXCLUDE_WORDS):
        return False
    for t in tag_list:
        t = t.lower()
        if f", {t}," in c or f"- {t}," in c or c.endswith(f", {t}") or c.endswith(f"- {t}"):
            return False
    return True


def music_comments():
    js = ('var l=Application("Music").libraryPlaylists[0].tracks;'
          'JSON.stringify([l.persistentID(),l.comment(),l.mediaKind()])')
    r = subprocess.run(["osascript", "-l", "JavaScript", "-e", js], capture_output=True, text=True, check=True)
    ids, com, kind = json.loads(r.stdout)
    return [(i, c) for i, c, k in zip(ids, com, kind) if k in ("song", "music video")]


def criteria(tag_list):
    s = copy.deepcopy(parse(TEMPLATE))
    inner = s["rules"][1]["payload"]          # ALL [ ANY[...], not Ignore ]  -> ALL [ not-tag rules..., not Ignore/Archive ]
    rules = []
    for t in tag_list:
        rules += [rule(NOT_CONTAINS, f", {t},"), rule(NOT_CONTAINS, f"- {t},"),
                  rule(NOT_ENDS, f", {t}"), rule(NOT_ENDS, f"- {t}")]
    rules += [rule(NOT_CONTAINS, w) for w in EXCLUDE_WORDS]
    inner["rules"] = rules
    inner["conj"] = 0
    return enc(s)


def main():
    tl = tags()
    tracks = music_comments()
    want = [(i, c) for i, c in tracks if is_untagged(c, tl)]
    kinds = {"empty comment": 0, "analysed, no tags": 0, "other text": 0}
    for _, c in want:
        c = (c or "").strip()
        if not c:
            kinds["empty comment"] += 1
        elif re.match(r"^\d{1,2}[AB]\s*-\s*\d+", c):
            kinds["analysed, no tags"] += 1
        else:
            kinds["other text"] += 1
    print(f"{len(tl)} tags; {len(tracks)} music tracks; expected in '{NAME}': {len(want)} {kinds}")
    json.dump([i for i, _ in want], open("/tmp/to_tag_expected.json", "w"))
    if "--check" in sys.argv:
        return
    pl = {"Name": NAME, "Playlist Persistent ID": pid(), "All Items": True,
          "Smart Info": SMART_INFO, "Smart Criteria": criteria(tl)}
    with open(OUT, "wb") as f:
        plistlib.dump({"Major Version": 1, "Minor Version": 1, "Date": datetime.datetime.now(), "Tracks": {},
                       "Playlists": [pl]}, f)
    if "--no-import" in sys.argv:
        return
    subprocess.run(["osascript", "-e", f'tell application "Music" to delete (every user playlist whose name is "{NAME}" and smart is true)'])
    imp = f'''tell application "Music" to activate
delay 1
tell application "System Events" to tell process "Music"
  click menu item "Import Playlist…" of menu 1 of menu item "Library" of menu 1 of menu bar item "File" of menu bar 1
  delay 2
  keystroke "g" using {{command down, shift down}}
  delay 1
  keystroke "{OUT}"
  delay 1
  key code 36
  delay 1.5
  key code 36
end tell'''
    subprocess.run(["osascript", "-e", imp])
    print("Imported. Verify with --check counts vs Music.")


if __name__ == "__main__":
    main()
