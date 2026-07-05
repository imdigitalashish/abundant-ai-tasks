#!/usr/bin/env python3
"""Pull long-tail deep repos from the SEART GitHub Search API.

Profile: 300-15k stars, >=50 contributors, >=300 issues, >=500 PRs,
active in 2026, not a fork. One sweep per language.
"""

import json
import subprocess
import sys
import time
import urllib.parse

BASE = "https://seart-ghs.si.usi.ch/api/r/search"
LANGUAGES = [
    "Python", "C", "C++", "Rust", "Go", "Java", "TypeScript", "JavaScript",
    "Ruby", "C#", "Kotlin", "Scala", "Haskell", "Elixir", "Julia", "PHP",
    "Swift", "OCaml", "Erlang", "Zig",
]
PARAMS = {
    "starsMin": 300, "starsMax": 15000,
    "contributorsMin": 50, "issuesMin": 300, "pullsMin": 500,
    "committedMin": "2026-01-01", "excludeForks": "true",
}
FIELDS = ["name", "mainLanguage", "stargazers", "contributors", "totalIssues",
          "openIssues", "totalPullRequests", "codeLines", "createdAt", "pushedAt",
          "license", "homepage"]


def fetch(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    out = subprocess.run(["curl", "-s", "--max-time", "30", url],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def main():
    out = {}
    for lang in LANGUAGES:
        rows, page, fails = [], 0, 0
        while True:
            try:
                d = fetch({**PARAMS, "language": lang, "page": page, "size": 100})
            except Exception as e:
                print(f"  {lang} page {page}: {e}", file=sys.stderr)
                fails += 1
                if fails > 3:
                    break
                time.sleep(5)
                continue
            items = d.get("items", [])
            rows += [{k: r.get(k) for k in FIELDS} for r in items]
            if d.get("last") or not items:
                break
            page += 1
            time.sleep(0.4)
        out[lang] = rows
        print(f"{lang:<12} {len(rows):>5} repos", file=sys.stderr)
        time.sleep(0.4)

    json.dump(out, sys.stdout)


if __name__ == "__main__":
    main()
