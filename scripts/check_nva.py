#!/usr/bin/env python3
"""Compare Tarjei's NVA records with data/nva_known.json and report new ones.

Writes a Markdown list of records not yet reviewed to --out, and new_count=<n>
to $GITHUB_OUTPUT when run in GitHub Actions. Exits 0 in every normal case.

  python scripts/check_nva.py --out new.md
  python scripts/check_nva.py --fixture sample.json --out new.md   (offline test)
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PERSON = "https://api.nva.unit.no/cristin/person/1103479"
API = "https://api.nva.unit.no/search/resources"
PAGE = 100


def fetch_all():
    hits, start = [], 0
    while True:
        url = f"{API}?contributor={PERSON}&results={PAGE}&from={start}"
        req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                   "User-Agent": "tarjeros.no-site-check"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
        batch = data.get("hits", [])
        hits.extend(batch)
        start += len(batch)
        if not batch or start >= int(data.get("totalHits", 0)):
            return hits


def describe(hit):
    ed = hit.get("entityDescription", {}) or {}
    title = ed.get("mainTitle", "(untitled)")
    year = ((ed.get("publicationDate") or {}).get("year")) or ""
    kind = (((ed.get("reference") or {}).get("publicationInstance") or {}).get("type")) or ""
    ident = hit.get("identifier", "")
    return ident, f"- **{title}** ({year}, {kind}) — https://nva.sikt.no/registration/{ident}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="new.md")
    ap.add_argument("--fixture", help="read NVA hits from a local JSON file instead of the API")
    args = ap.parse_args()

    known = {r["id"] for r in json.loads((ROOT / "data" / "nva_known.json").read_text(encoding="utf-8"))["records"]}
    hits = json.loads(Path(args.fixture).read_text(encoding="utf-8"))["hits"] if args.fixture else fetch_all()

    new = [describe(h) for h in hits if h.get("identifier") and h["identifier"] not in known]
    lines = [
        f"NVA has {len(new)} record(s) that are not yet reviewed for tarjeros.no:",
        "",
        *[line for _, line in new],
        "",
        "To update the site: decide which of these belong on the page, then add every id below to "
        "`data/nva_known.json` (also the ones you leave off) so they stop being reported.",
        "",
        "```",
        *[ident for ident, _ in new],
        "```",
    ]
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(hits)} NVA records, {len(new)} new")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"new_count={len(new)}\n")


if __name__ == "__main__":
    sys.exit(main())
