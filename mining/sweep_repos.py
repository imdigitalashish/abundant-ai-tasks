#!/usr/bin/env python3
"""Sweep a list of candidate repos and rank them for SWE-gen farming value.

For each repo: scan recent merged PRs, apply swegen filters, report
yield (% usable) and mean hardness of the top-5 usable PRs.

Usage: python3 sweep_repos.py [--pages N] repo1 repo2 ...
       python3 sweep_repos.py --file repos.txt
"""

import argparse
import concurrent.futures as cf
import json
import statistics
import time

from score_prs import fetch_prs, score_pr


def sweep(repo: str, pages: int, delay: float = 0.0):
    if delay:
        time.sleep(delay)
    owner, name = repo.split("/")
    kept, total, no_issue = [], 0, 0
    try:
        for pr in fetch_prs(owner, name, pages):
            total += 1
            row, why = score_pr(pr)
            if row:
                kept.append(row)
            elif why == "no-issue":
                no_issue += 1
    except Exception as e:
        return {"repo": repo, "error": str(e)}
    kept.sort(key=lambda r: -r["score"])
    top5 = [r["score"] for r in kept[:5]]
    return {
        "repo": repo,
        "scanned": total,
        "usable": len(kept),
        "yield_pct": round(100 * len(kept) / total, 1) if total else 0.0,
        "no_issue_pct": round(100 * no_issue / total, 1) if total else 0.0,
        "top5_hardness": round(statistics.mean(top5), 1) if top5 else 0.0,
        "best_prs": [r["number"] for r in kept[:5]],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="*")
    ap.add_argument("--file", help="file with one owner/repo per line")
    ap.add_argument("--pages", type=int, default=2)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--delay", type=float, default=0.0,
                    help="seconds to sleep before each repo (rate-limit safety)")
    ap.add_argument("--json", action="store_true", help="emit results as JSON")
    args = ap.parse_args()

    repos = list(args.repos)
    if args.file:
        with open(args.file) as f:
            repos += [l.strip() for l in f if l.strip() and not l.startswith("#")]

    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(lambda r: sweep(r, args.pages, args.delay), repos))

    if args.json:
        print(json.dumps(results))
        return

    ok = [r for r in results if "error" not in r]
    # farming value = how many hard tasks you get per unit of farming effort
    ok.sort(key=lambda r: -(r["usable"] * r["top5_hardness"]))

    hdr = (f"{'repo':<28} {'scan':>5} {'usable':>6} {'yield%':>6} "
           f"{'noIss%':>6} {'top5-hard':>9}  best PRs")
    print(hdr)
    print("-" * len(hdr))
    for r in ok:
        print(f"{r['repo']:<28} {r['scanned']:>5} {r['usable']:>6} "
              f"{r['yield_pct']:>6} {r['no_issue_pct']:>6} {r['top5_hardness']:>9}  "
              f"{','.join(map(str, r['best_prs']))}")
    for r in results:
        if "error" in r:
            print(f"{r['repo']:<28} ERROR: {r['error']}")


if __name__ == "__main__":
    main()
