#!/usr/bin/env python3
"""Build Music smart playlists, one per tag in Library_Manager's Genre.xlsx.

Folder layout: <ROOT>/<NN column name>/<tag>. Each playlist's rule is: comment contains the tag as a
whole word (", Tag," / "- Tag," / ends with ", Tag" / "- Tag") AND comment does not contain "Ignore"
(except the Ignore column). Built by Hermes from Dan's own smart playlist (01 Genres/House/All) as template.

Usage (Library_Manager venv has openpyxl):
  venv/bin/python tools/make_tag_playlists.py   (run from the Library_Manager folder) [--replace] [--no-dates | --dates-only] [--no-import]
Builds 09 Tags, 10 Ignore (Ignore + Archive, outside 09 Tags so rekordbox can untick it) and 06 Date (by Date Added,
see make_date_playlists.py; --no-dates skips it, --dates-only builds/replaces only 06 Date). --replace deletes those folders in Music first (otherwise duplicates are imported).
"""
import copy, os, plistlib, secrets, struct, subprocess, sys, datetime
import openpyxl

XLSX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Genre.xlsx")
ROOT = "09 Tags"
EXCLUDED_ROOT = "10 Ignore"      # separate top-level folder so rekordbox can untick it (no auto import)
EXCLUDED_COLUMNS = {"Ignore"}    # columns whose playlists (Ignore, Archive) go there, not into ROOT
OUT = "/tmp/music_tag_playlists.xml"
EXTRA_SPELLINGS = {"Big Beat": ["Big Beat", "Big-Beat"]}
NO_IGNORE_FILTER_COLUMNS = {"Ignore"}
# Tags matched as plain substring, case-insensitive like every other "does not contain Ignore" filter. Whole-word matching
# missed ~7500 tracks whose comment is just "Ignore"/"IGNORE\n", so they were in no playlist and the Ignore playlist undercounted.
SUBSTRING_TAGS = {"Ignore"}
TEMPLATE = bytes.fromhex("534c73740001000100000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000180534c73740001000100000002000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003c0000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004400000000000000010000000000000000000000000000000100000000000000010000000000000000000000000000000100000000000000000000000000000000000000000000003c0000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004400000000000000200000000000000000000000000000000100000000000000200000000000000000000000000000000100000000000000000000000000000000000000000000000000000001010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000262534c7374000100010000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000101000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000015e534c73740001000100000003000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e01000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010002c00200048006f007500730065002c0000000e01000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010002d00200048006f007500730065002c0000000e0100000800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e002c00200048006f0075007300650000000e0300000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c00490067006e006f00720065")
SMART_INFO = bytes.fromhex("01010003000000020000001900000000000000070000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")
HDR = 136
CONTAINS, ENDS = 0x01000002, 0x01000008

def parse(b):
    n, conj = struct.unpack(">II", b[8:16]); pos = HDR; rules = []
    for _ in range(n):
        f, op = struct.unpack(">II", b[pos:pos+8]); extra = b[pos+8:pos+52]
        L = struct.unpack(">I", b[pos+52:pos+56])[0]; p = b[pos+56:pos+56+L]; pos += 56 + L
        if f == 0 and p[:4] == b"SLst": p = parse(p)
        rules.append({"field": f, "op": op, "extra": extra, "payload": p})
    return {"head": b[:HDR], "conj": conj, "rules": rules}

def enc(s):
    h = bytearray(s["head"]); h[8:16] = struct.pack(">II", len(s["rules"]), s["conj"]); out = bytes(h)
    for r in s["rules"]:
        p = r["payload"]; p = enc(p) if isinstance(p, dict) else p
        out += struct.pack(">II", r["field"], r["op"]) + r["extra"] + struct.pack(">I", len(p)) + p
    return out

def rule(op, v): return {"field": 0xE, "op": op, "extra": bytes(44), "payload": v.encode("utf-16-be")}

def criteria(spellings, ignore_filter, substring=False):
    s = copy.deepcopy(parse(TEMPLATE)); inner = s["rules"][1]["payload"]
    if substring:
        inner["rules"][0]["payload"]["rules"] = [rule(CONTAINS, t) for t in spellings]
    else:
        inner["rules"][0]["payload"]["rules"] = [r for t in spellings for r in (
            rule(CONTAINS, f", {t},"), rule(CONTAINS, f"- {t},"), rule(ENDS, f", {t}"), rule(ENDS, f"- {t}"))]
    if not ignore_filter: inner["rules"] = inner["rules"][:1]
    return enc(s)

def pid(): return secrets.token_hex(8).upper()

def main():
    ws = openpyxl.load_workbook(XLSX).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    cols = [str(c).lstrip("\ufeff").strip() for c in rows[0]]
    only_dates = "--dates-only" in sys.argv
    root = pid(); pls = [{"Name": ROOT, "Folder": True, "Playlist Persistent ID": root, "All Items": True}]
    xroot = pid(); pls.append({"Name": EXCLUDED_ROOT, "Folder": True, "Playlist Persistent ID": xroot, "All Items": True})
    if only_dates: pls = []   # keep the tag code, just don't emit it
    n = 0
    for i, col in enumerate(cols):
        if only_dates: break
        tags = [str(r[i]).strip() for r in rows[1:] if i < len(r) and r[i]]
        if not tags: continue
        if col in EXCLUDED_COLUMNS:
            fid = xroot  # playlists go straight into the excluded folder, no sub-folder
        else:
            fid = pid()
            pls.append({"Name": f"{i+1:02d} {col}", "Folder": True, "Playlist Persistent ID": fid,
                        "Parent Persistent ID": root, "All Items": True})
        for t in tags:
            pls.append({"Name": t, "Playlist Persistent ID": pid(), "Parent Persistent ID": fid, "All Items": True,
                        "Smart Info": SMART_INFO,
                        "Smart Criteria": criteria(EXTRA_SPELLINGS.get(t, [t]), col not in NO_IGNORE_FILTER_COLUMNS, t in SUBSTRING_TAGS)})
            n += 1
    if "--no-dates" not in sys.argv or only_dates:  # also (re)build 06 Date from Date Added, see make_date_playlists.py
        import make_date_playlists
        pls += make_date_playlists.build_entries()
    with open(OUT, "wb") as f:
        plistlib.dump({"Major Version": 1, "Minor Version": 1, "Date": datetime.datetime.now(), "Tracks": {},
                       "Playlists": pls}, f)
    print(f"Wrote {n} smart playlists to {OUT}")
    if "--replace" in sys.argv:
      for ROOT_ in (() if only_dates else (ROOT, EXCLUDED_ROOT)) + (() if ("--no-dates" in sys.argv and not only_dates) else ("06 Date",)):
        subprocess.run(["osascript", "-e", f'tell application "Music" to if exists folder playlist "{ROOT_}" then delete folder playlist "{ROOT_}"'])
    if "--no-import" not in sys.argv:
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
        print("Imported into Music (needs Accessibility permission for the app running this).")

if __name__ == "__main__":
    main()
