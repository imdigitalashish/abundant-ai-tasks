#!/usr/bin/env python3
"""Score merged PRs of a repo for SWE-gen "hardness".

Hard filters (mirror swegen defaults):
  - merged PR with a linked (closing) issue
  - touches >=1 test file AND 3-10 non-test source files

Hardness score = proxies for:
  - reasoning  : issue discussion volume, issue/PR body length
  - change size: source LOC delta (log), source file count
  - iteration  : PR commit count, review threads, PR comments

Usage: python3 score_prs.py owner/repo [--pages N] [--top K]
Requires: gh CLI authenticated.
"""

import argparse
import json
import math
import re
import subprocess
import sys

QUERY = """
query($owner:String!, $name:String!, $cursor:String) {
  repository(owner:$owner, name:$name) {
    pullRequests(states: MERGED, first: 50, after: $cursor,
                 orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title mergedAt additions deletions changedFiles
        bodyText
        totalCommentsCount
        commits { totalCount }
        reviewThreads { totalCount }
        closingIssuesReferences(first: 3) {
          totalCount
          nodes { number bodyText comments { totalCount } }
        }
        files(first: 60) { nodes { path additions deletions } }
      }
    }
  }
}
"""

TEST_RE = re.compile(
    r"(^|/)(tests?|testing|spec|specs|__tests__)(/|$)|_test\.[a-z]+$|\.test\.|\.spec\.|^conftest\.py$|(^|/)conftest\.py$",
    re.I,
)
NON_SOURCE_RE = re.compile(
    r"\.(md|rst|txt|adoc|lock|sum|mod|toml|cfg|ini|json|ya?ml|svg|png|jpg|gif|csv)$"
    r"|(^|/)(docs?|examples?|benchmarks?|\.github|changelog)(/|$)",
    re.I,
)


def classify(path: str) -> str:
    if TEST_RE.search(path):
        return "test"
    if NON_SOURCE_RE.search(path):
        return "other"
    return "source"


def fetch_prs(owner: str, name: str, pages: int):
    cursor = None
    for _ in range(pages):
        cmd = [
            "gh", "api", "graphql",
            "-f", f"query={QUERY}",
            "-f", f"owner={owner}",
            "-f", f"name={name}",
        ]
        if cursor:
            cmd += ["-f", f"cursor={cursor}"]
        out = subprocess.run(cmd, capture_output=True, text=True)
        if out.returncode != 0:
            print(out.stderr, file=sys.stderr)
            break
        data = json.loads(out.stdout)["data"]["repository"]["pullRequests"]
        yield from data["nodes"]
        if not data["pageInfo"]["hasNextPage"]:
            break
        cursor = data["pageInfo"]["endCursor"]


def score_pr(pr: dict):
    files = pr["files"]["nodes"]
    src = [f for f in files if classify(f["path"]) == "source"]
    tst = [f for f in files if classify(f["path"]) == "test"]

    issues = pr["closingIssuesReferences"]
    if issues["totalCount"] == 0:
        return None, "no-issue"
    if not tst:
        return None, "no-tests"
    if not (3 <= len(src) <= 10):
        return None, f"src-files={len(src)}"

    src_loc = sum(f["additions"] + f["deletions"] for f in src)
    issue_comments = sum(i["comments"]["totalCount"] for i in issues["nodes"])
    issue_body = sum(len(i["bodyText"]) for i in issues["nodes"])
    commits = pr["commits"]["totalCount"]
    threads = pr["reviewThreads"]["totalCount"]
    pr_comments = pr["totalCommentsCount"]

    score = (
        2.0 * math.log2(1 + src_loc)          # change size (log-scaled)
        + 1.5 * len(src)                       # breadth across source files
        + 1.0 * min(commits, 20)               # iteration loops
        + 1.5 * min(threads, 20)               # review back-and-forth
        + 0.5 * min(pr_comments, 20)           # discussion
        + 1.0 * min(issue_comments, 20)        # reasoning: issue debate
        + 0.5 * math.log2(1 + issue_body)      # reasoning: issue depth
    )
    return {
        "number": pr["number"],
        "title": pr["title"][:70],
        "merged": pr["mergedAt"][:10],
        "src_files": len(src),
        "test_files": len(tst),
        "src_loc": src_loc,
        "commits": commits,
        "threads": threads,
        "issue_comments": issue_comments,
        "score": round(score, 1),
    }, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", help="owner/repo")
    ap.add_argument("--pages", type=int, default=4, help="pages of 50 PRs")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--json", action="store_true", help="emit full JSON")
    args = ap.parse_args()

    owner, name = args.repo.split("/")
    kept, rejected = [], {}
    total = 0
    for pr in fetch_prs(owner, name, args.pages):
        total += 1
        row, why = score_pr(pr)
        if row:
            kept.append(row)
        else:
            rejected[why] = rejected.get(why, 0) + 1

    kept.sort(key=lambda r: -r["score"])
    yield_pct = 100 * len(kept) / total if total else 0
    print(f"\n{args.repo}: scanned {total} merged PRs, "
          f"{len(kept)} pass swegen filters ({yield_pct:.0f}% yield)")
    print(f"rejections: {rejected}\n")

    if args.json:
        print(json.dumps(kept, indent=2))
        return

    hdr = f"{'score':>6} {'PR#':>6} {'merged':>10} {'src':>3} {'tst':>3} {'LOC':>5} {'cmt':>3} {'rev':>3} {'iss':>3}  title"
    print(hdr)
    print("-" * len(hdr))
    for r in kept[: args.top]:
        print(f"{r['score']:>6} {r['number']:>6} {r['merged']:>10} "
              f"{r['src_files']:>3} {r['test_files']:>3} {r['src_loc']:>5} "
              f"{r['commits']:>3} {r['threads']:>3} {r['issue_comments']:>3}  {r['title']}")


if __name__ == "__main__":
    main()
