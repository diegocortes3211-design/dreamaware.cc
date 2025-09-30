#!/usr/bin/env python3
import os, sys, json, subprocess, math
from collections import defaultdict

REPO = os.environ.get("GITHUB_REPOSITORY") # e.g. diegocortes3211-design/dreamaware.cc

def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr.strip(), file=sys.stderr)
        sys.exit(r.returncode)
    return r.stdout

def get_open_prs():
    out = gh("api", f"repos/{REPO}/pulls?state=open&per_page=100")
    return json.loads(out)

def get_files(pr_number):
    out = gh("api", f"repos/{REPO}/pulls/{pr_number}/files?per_page=200")
    return [f["filename"] for f in json.loads(out)]

def jaccard(a, b):
    sa, sb = set(a), set(b)
    inter = len(sa & sb); union = len(sa | sb) or 1
    return inter/union, inter

def main():
    prs = get_open_prs()
    pr_files = {}
    for pr in prs:
        pr_files[pr["number"]] = get_files(pr["number"])

    # Compute pairwise overlap and a simple risk score
    risk = {}
    for i in prs:
        i_num = i["number"]; i_files = pr_files[i_num]
        max_j, max_inter = 0.0, 0
        for j in prs:
            if j["number"] == i_num: continue
            jacc, inter = jaccard(i_files, pr_files[j["number"]])
            if jacc > max_j:
                max_j, max_inter = jacc, inter

        # Heuristic thresholds
        if max_inter >= 6 or max_j >= 0.30:
            level = "conflicts:high"
        elif max_inter >= 3 or max_j >= 0.15:
            level = "conflicts:medium"
        else:
            level = "conflicts:low"
        risk[i_num] = level

    # Batch by primary area label + risk (low first)
    # Fetch labels for each PR
    areas = ["infra","security","ucapi","slack","dreadapi","agentics","video","docs","monorepo-refactor","rekor"]
    def primary_area(labels):
        names = [l["name"] for l in labels]
        for a in areas:
            if a in names: return a
        return "misc"

    buckets = defaultdict(list)
    for pr in prs:
        pr_labels = pr.get("labels", [])
        buckets[(primary_area(pr_labels), risk[pr["number"]])].append(pr)

    # Emit plan.md
    lines = ["# Merge Plan\n"]
    order = [
        ("docs","conflicts:low"), ("ucapi","conflicts:low"), ("slack","conflicts:low"),
        ("dreadapi","conflicts:low"), ("agentics","conflicts:low"), ("video","conflicts:low"),
        ("rekor","conflicts:low"), ("security","conflicts:low"), ("infra","conflicts:low"),
        # then mediums, then highs
    ]
    for a in areas: order.append((a,"conflicts:medium"))
    for a in areas: order.append((a,"conflicts:high"))

    batch_id = 1
    for key in order:
        prs_here = buckets.get(key, [])
        if not prs_here: continue
        lines.append(f"## Batch {batch_id} — {key[0]} • {key[1]}")
        for pr in sorted(prs_here, key=lambda x: x["number"]):
            lines.append(f"- #{pr['number']} {pr['title']}")
        lines.append("")
        batch_id += 1

    with open("tools/triage/merge_plan.md","w") as f:
        f.write("\n".join(lines))

    # Apply risk labels to PRs
    for pr in prs:
        lvl = risk[pr["number"]]
        gh("pr", "edit", str(pr["number"]), "--add-label", lvl)

    print("Wrote tools/triage/merge_plan.md and labeled PRs with conflict risk.")

if __name__ == "__main__":
    if not REPO:
        print("Set GITHUB_REPOSITORY (owner/repo).", file=sys.stderr); sys.exit(1)
    main()
