#!/usr/bin/env python3
"""Compute the review-full overall score from resolver output and domain scores.

Usage:
  python3 overall.py --resolver resolver.txt --scores "architecture=7.2,security=8,data=N/A,..." [--critical]

--resolver   saved stdout of `fitness-config.py show --path <target>` (repeat the
             flag once per config group when a diff spans several configs).
--scores     every reviewed domain as name=X.X; use N/A for skipped, weight-0,
             all-N/A, or failed domains. Missing domains are treated as N/A.
--critical   at least one CRITICAL finding exists: cap the overall at 4.0.

Prints, per config group, the status of each domain, the weighted arithmetic,
and the overall. With several groups the headline overall is the lowest group
overall. Standard library only.
"""
import argparse
import json
import re
import sys

DOMAINS = [
    "architecture", "security", "reliability", "testing", "performance",
    "algorithms", "data", "accessibility", "process", "maintainability",
]
BEGIN = "<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->"
END = "<!-- END_EFFECTIVE_CONFIG_JSON -->"


def load_group(path):
    text = open(path, encoding="utf-8").read()
    if BEGIN not in text or END not in text:
        sys.exit(f"{path}: no effective-config JSON block; save the full `show --path` output")
    block = text.split(BEGIN, 1)[1].split(END, 1)[0]
    block = re.sub(r"^\s*```(json)?\s*$", "", block, flags=re.M)
    data = json.loads(block)
    eff = data["effective"]
    config_line = next((ln for ln in text.splitlines() if ln.startswith("Config:")), "Config: ?")
    weights = eff["weights"]
    total = sum(weights.values())
    if total != 100:
        sys.exit(f"{path}: weights sum to {total}, not 100; run `validate --path` and fix the config")
    return config_line, weights, eff.get("statusThresholds", {})


def status(score, thresholds):
    healthy = thresholds.get("healthy", [8, 10])[0]
    attention = thresholds.get("needsAttention", [5, 7])[0]
    if score >= healthy:
        return "Healthy"
    if score >= attention:
        return "Needs Attention"
    return "Critical"


def parse_scores(raw):
    scores = {}
    for part in filter(None, (p.strip() for p in raw.split(","))):
        name, _, value = part.partition("=")
        name = name.strip().lower()
        if name not in DOMAINS:
            sys.exit(f"unknown domain: {name}")
        value = value.strip()
        if value.upper() in ("N/A", "NA", "SKIPPED", ""):
            scores[name] = None
        else:
            v = float(value)
            if not 1 <= v <= 10:
                sys.exit(f"{name}={v} is outside 1-10")
            scores[name] = v
    return scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resolver", action="append", required=True)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--critical", action="store_true")
    args = ap.parse_args()
    scores = parse_scores(args.scores)

    overalls = []
    for path in args.resolver:
        config_line, weights, thresholds = load_group(path)
        scored = [(d, weights[d], scores[d]) for d in DOMAINS
                  if scores.get(d) is not None and weights.get(d, 0) > 0]
        if not scored:
            sys.exit("no scored domains with weight > 0")
        num = sum(w * s for _, w, s in scored)
        den = sum(w for _, w, _ in scored)
        raw = num / den
        overall = min(raw, 4.0) if args.critical else raw
        overalls.append(overall)
        print(config_line)
        for d in DOMAINS:
            s = scores.get(d)
            w = weights.get(d, 0)
            if s is None or w == 0:
                print(f"  {d:<16} N/A   weight {w}")
            else:
                print(f"  {d:<16} {s:.1f}  weight {w}  {status(s, thresholds)}")
        terms = " + ".join(f"{w}*{s:.1f}" for _, w, s in scored)
        print(f"  Arithmetic: ({terms}) / {den} = {num:.1f} / {den} = {raw:.2f}")
        if args.critical and raw > 4.0:
            print("  CRITICAL finding present: capped at 4.0")
        print(f"  Overall: {overall:.1f} ({status(overall, thresholds)})")
    if len(overalls) > 1:
        print(f"Headline overall (lowest group): {min(overalls):.1f}")


if __name__ == "__main__":
    main()
