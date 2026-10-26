#!/usr/bin/env python3
"""Link Dan's vignette tracks as rekordbox "Matching" pairs, in story order (1<->2, 2<->3, 3<->4).

Vignettes come from the Music app's Grouping field: "#Vignette Name N" (N = position).
rekordbox stores Matching pairs in master.db table djmdRecommendLike.

Run with the rekordbox venv (has pyrekordbox), rekordbox CLOSED:
  ~/rekordbox-automation/venv/bin/python tools/link_vignettes.py              # dry run, shows plan
  ~/rekordbox-automation/venv/bin/python tools/link_vignettes.py --write      # back up master.db, then write
  ... --only "#Synergy Techno Opener"                                         # limit to one vignette

Only adds pairs that don't exist yet (either direction). Links it creates are recorded in
~/rekordbox-automation/vignette_links.json so they can be found/removed later; manual links are never touched.
"""
import datetime, json, os, re, shutil, subprocess, sys, unicodedata, uuid
from collections import defaultdict

import sqlalchemy as sa
from pyrekordbox import Rekordbox6Database

STATE = os.path.expanduser("~/rekordbox-automation/vignette_links.json")
JXA = r"""
const tr = Application('Music').libraryPlaylists[0].fileTracks;
const g = tr.grouping(), loc = tr.location(), nm = tr.name(), ar = tr.artist();
let out = [];
g.forEach((x,i) => { if (x && x.trim().startsWith('#')) out.push([x, loc[i] ? loc[i].toString() : null, ar[i], nm[i]]); });
JSON.stringify(out);
"""


def norm(s):
    return unicodedata.normalize("NFC", s or "").lower()


def read_vignettes():
    raw = subprocess.run(["osascript", "-l", "JavaScript", "-e", JXA], capture_output=True, text=True, check=True).stdout
    groups = defaultdict(list)
    for g, path, artist, title in json.loads(raw):
        m = re.match(r"^\s*(#.*?)\s*(\d+)?\s*$", g)
        groups[m.group(1).strip()].append(
            {"pos": int(m.group(2)) if m.group(2) else None, "path": path, "label": f"{artist} - {title}"})
    return groups


def main():
    write = "--write" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    if write and subprocess.run(["pgrep", "-x", "rekordbox"], capture_output=True).returncode == 0:
        sys.exit("rekordbox is running - close it first.")

    db = Rekordbox6Database()
    by_path = {}
    for c in db.get_content():
        by_path.setdefault(norm(c.FolderPath), c.ID)
    existing = {frozenset((str(a), str(b))) for a, b in db.session.execute(
        sa.text("select ContentID1, ContentID2 from djmdRecommendLike where rb_local_deleted = 0"))}

    plan, problems = [], []
    for name, items in sorted(read_vignettes().items()):
        if only and name != only:
            continue
        if any(i["pos"] is None for i in items):
            problems.append(f"{name}: no position numbers in Grouping, skipped")
            continue
        items.sort(key=lambda i: i["pos"])
        for i in items:
            i["id"] = by_path.get(norm(i["path"]))
        missing = [i["label"] for i in items if not i["id"]]
        if missing:
            problems.append(f"{name}: not in rekordbox: {missing}, skipped")
            continue
        for a, b in zip(items, items[1:]):
            state = "exists" if frozenset((a["id"], b["id"])) in existing else "NEW"
            plan.append((name, a, b, state))

    for name, a, b, state in plan:
        print(f"[{state}] {name}: {a['pos']} {a['label']}  <->  {b['pos']} {b['label']}")
    for p in problems:
        print("SKIP", p)
    new = [p for p in plan if p[3] == "NEW"]
    print(f"\n{len(new)} new links, {len(plan) - len(new)} already present.")
    if not write or not new:
        print("Dry run - nothing written." if not write else "Nothing to write.")
        return

    src = db.db_directory / "master.db" if hasattr(db, "db_directory") else None
    src = str(src) if src else os.path.expanduser("~/Library/Pioneer/rekordbox/master.db")
    backup = f"{src}.backup-vignettes-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    shutil.copy2(src, backup)
    print("Backup:", backup)

    now = datetime.datetime.now(datetime.timezone.utc)
    ms = int(now.timestamp() * 1000)
    stamp = now.strftime("%Y-%m-%d %H:%M:%S.") + f"{now.microsecond // 1000:03d} +00:00"
    created = []
    for name, a, b, _ in new:
        usn = db.increment_local_usn(1)
        row = {"ID": str(uuid.uuid4()), "UUID": str(uuid.uuid4()), "c1": a["id"], "c2": b["id"],
               "H": ms >> 32, "L": ms & 0xFFFFFFFF, "usn": usn, "ts": stamp}
        db.session.execute(sa.text(
            "insert into djmdRecommendLike (ID, ContentID1, ContentID2, LikeRate, DataCreatedH, DataCreatedL, UUID, "
            "rb_data_status, rb_local_data_status, rb_local_deleted, rb_local_synced, usn, rb_local_usn, created_at, updated_at) "
            "values (:ID, :c1, :c2, NULL, :H, :L, :UUID, 0, 0, 0, 0, NULL, :usn, :ts, :ts)"), row)
        created.append({"vignette": name, "ID": row["ID"], "pair": [a["label"], b["label"]], "content_ids": [a["id"], b["id"]]})
    db.commit(autoinc=False)

    log = json.load(open(STATE)) if os.path.exists(STATE) else []
    json.dump(log + created, open(STATE, "w"), indent=1, ensure_ascii=False)

    check = Rekordbox6Database()
    ids = {r[0] for r in check.session.execute(sa.text("select ID from djmdRecommendLike"))}
    ok = all(c["ID"] in ids for c in created)
    print(f"Wrote {len(created)} links; verified after reopen: {ok}")


if __name__ == "__main__":
    main()
