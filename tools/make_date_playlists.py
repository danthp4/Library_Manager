#!/usr/bin/env python3
"""Build the `06 Date` smart playlists in Music: one folder per year, playlists by Date Added.

Rule per playlist: Date Added in [first day of first month, last day of last month] AND comment does not
contain "Ignore" (same as Dan's hand-made ones, copied from his `Aug 19`). Months with fewer than MIN_TRACKS
(5) non-Ignore tracks are merged with the following month(s) of the same year until the group reaches 5; a
short tail at the end of a year merges into the previous group. Empty single-month playlists are pre-created up to
--through (default 2027-12); re-run later and under-5 months get merged. (With --through before the last month, the last group runs to 31 Dec.)

Usage (run from the Library_Manager folder, Music must be open):
  python3 tools/make_date_playlists.py [--from 2019-06] [--min 5] [--through 2027-12] [--no-import] [--replace]
Without --no-import it prints the plan, writes /tmp/music_date_playlists.xml and imports it (UI scripting).
--replace deletes the existing `06 Date` folder first. Re-apply the view afterwards:
  osacompile -o /tmp/av.scpt tools/apply_playlist_view.applescript; osascript /tmp/av.scpt
"""
import calendar, collections, copy, datetime, json, os, plistlib, secrets, struct, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_tag_playlists import parse, enc, pid

ROOT = "06 Date"
OUT = "/tmp/music_date_playlists.xml"
TEMPLATE = bytes.fromhex("534c73740001000100000002000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000180534c73740001000100000002000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003c0000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004400000000000000010000000000000000000000000000000100000000000000010000000000000000000000000000000100000000000000000000000000000000000000000000003c0000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004400000000000000200000000000000000000000000000000100000000000000200000000000000000000000000000000100000000000000000000000000000000000000000000000000000001010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000148534c7374000100010000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000004400000000d967dc000000000000000000000000000000000100000000d990ba7f0000000000000000000000000000000100000000000000000000000000000000000000000000000e0300000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c00490067006e006f00720065")  # criteria of Dan's `Aug 19`
SMART_INFO = bytes.fromhex("01010003000000150000001900000000000000070000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000")  # Smart Info of Dan's `Aug 19`
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]
MAC_EPOCH = datetime.datetime(1904, 1, 1)

def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default

def fetch_months():
    """{(year, month): number of tracks added that month without 'Ignore' in the comment} from Music."""
    js = ('const t=Application("Music").libraryPlaylists[0].tracks;'
          'JSON.stringify({d:t.dateAdded().map(x=>x.getFullYear()*100+x.getMonth()+1),c:t.comment()})')
    d = json.loads(subprocess.run(["osascript", "-l", "JavaScript", "-e", js], capture_output=True, text=True, check=True).stdout)
    cnt = collections.Counter()
    for ym, c in zip(d["d"], d["c"]):
        if "ignore" not in (c or "").lower():  # Music matches case-insensitively
            cnt[(ym // 100, ym % 100)] += 1
    return cnt

def plan(cnt, start, min_tracks):
    """-> {year: [(first_month, last_month, tracks)]}"""
    out = {}
    for y in sorted({y for y, m in cnt if (y, m) >= start}):
        groups, cur = [], None
        for m in range(1, 13):
            n = cnt.get((y, m), 0)
            if (y, m) < start or n == 0:
                continue
            cur = [m, m, n] if cur is None else [cur[0], m, cur[2] + n]
            if cur[2] >= min_tracks:
                groups.append(cur); cur = None
        if cur:
            if groups: groups[-1] = [groups[-1][0], cur[1], groups[-1][2] + cur[2]]
            else: groups.append(cur)
        out[y] = [tuple(g) for g in groups]
    return out

def label(y, a, b):
    yy = f"{y % 100:02d}"
    return f"{MON[a-1]} {yy}" if a == b else f"{MON[a-1]}-{MON[b-1]} {yy}"

def mac(dt):  # Music stores local wall-clock seconds since 1904 for date rules
    return int((dt - MAC_EPOCH).total_seconds())

def criteria(y, a, b, last_of_year_open):
    start = datetime.datetime(y, a, 1)
    end_m = 12 if last_of_year_open else b
    end = datetime.datetime(y, end_m, calendar.monthrange(y, end_m)[1], 23, 59, 59)
    s = parse(TEMPLATE)
    for r in s["rules"][1]["payload"]["rules"]:
        if r["field"] == 0x10:  # unwrap: date rule sits inside the ALL[...] sub-list
            pass
    def fix(node):
        for r in node["rules"]:
            if isinstance(r["payload"], dict): fix(r["payload"])
            elif r["field"] == 0x10:
                p = bytearray(r["payload"]); p[0:8] = struct.pack(">Q", mac(start)); p[24:32] = struct.pack(">Q", mac(end))
                r["payload"] = bytes(p)
    fix(s)
    return enc(s)

def build_entries(start=None, min_tracks=None):
    """Playlist entries (folder 06 Date, year folders, smart playlists) for the import XML. Prints the plan."""
    start = start or tuple(int(x) for x in arg("--from", "2019-06").split("-"))
    pl = plan(fetch_months(), start, min_tracks or int(arg("--min", "5")))
    now = datetime.date.today()
    # Pre-create empty single-month playlists from the month after the last real one up to --through (default 2027-12),
    # so new tracks land in a ready playlist. A later run merges months that stay under the minimum.
    through = tuple(int(x) for x in arg("--through", "2027-12").split("-"))
    ly = max(pl); lm = pl[ly][-1][1]
    y, m = (ly, lm + 1) if lm < 12 else (ly + 1, 1)
    while (y, m) <= through:
        pl.setdefault(y, []).append((m, m, 0))
        y, m = (y, m + 1) if m < 12 else (y + 1, 1)
    root = pid(); pls = [{"Name": ROOT, "Folder": True, "Playlist Persistent ID": root, "All Items": True}]
    for y, groups in pl.items():
        fid = pid()
        pls.append({"Name": str(y), "Folder": True, "Playlist Persistent ID": fid, "Parent Persistent ID": root, "All Items": True})
        for i, (a, b, n) in enumerate(groups):
            open_end = (i == len(groups) - 1 and (y, groups[-1][1]) >= through)  # only if nothing is pre-created after it
            print(f"{y}  {label(y, a, b):14} {n:4} tracks" + ("  (runs to 31 Dec)" if open_end else "  (pre-created, empty)" if n == 0 else ""))
            pls.append({"Name": label(y, a, b), "Playlist Persistent ID": pid(), "Parent Persistent ID": fid, "All Items": True,
                        "Smart Info": SMART_INFO, "Smart Criteria": criteria(y, a, b, open_end)})
    return pls

def main():
    pls = build_entries()
    with open(OUT, "wb") as f:
        plistlib.dump({"Major Version": 1, "Minor Version": 1, "Date": datetime.datetime.now(), "Tracks": {}, "Playlists": pls}, f)
    print(f"Wrote {len(pls)} entries to {OUT}")
    if "--replace" in sys.argv and "--no-import" not in sys.argv:
        subprocess.run(["osascript", "-e", f'tell application "Music" to if exists folder playlist "{ROOT}" then delete folder playlist "{ROOT}"'])
    if "--no-import" not in sys.argv:
        imp = f"""tell application "Music" to activate
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
end tell"""
        subprocess.run(["osascript", "-e", imp])
        print("Imported into Music.")

if __name__ == "__main__":
    main()
