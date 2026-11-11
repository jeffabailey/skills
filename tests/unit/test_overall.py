"""skills/review-full/scripts/overall.py: the weighted overall and its status band."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "skills/review-full/scripts/overall.py"
DOMAINS = ["architecture", "security", "reliability", "testing", "performance",
           "algorithms", "data", "accessibility", "process", "maintainability"]


def resolver_file(tmp_path, weights, thresholds=None):
    effective = {"weights": weights}
    if thresholds is not None:
        effective["statusThresholds"] = thresholds
    path = tmp_path / "resolver.txt"
    path.write_text("Config: fitness-config.json\n<!-- BEGIN_EFFECTIVE_CONFIG_JSON -->\n"
                    + json.dumps({"effective": effective})
                    + "\n<!-- END_EFFECTIVE_CONFIG_JSON -->\n")
    return path


def run(resolver, scores, *flags):
    return subprocess.run([sys.executable, str(SCRIPT), "--resolver", str(resolver),
                           "--scores", scores, *flags], capture_output=True, text=True)


def two_domain_weights():
    return {d: (50 if d in ("architecture", "security") else 0) for d in DOMAINS}


def test_weighted_overall_skips_na_and_shows_arithmetic(tmp_path):
    weights = {d: 10 for d in DOMAINS}
    result = run(resolver_file(tmp_path, weights), "architecture=6,security=8,data=N/A")
    assert result.returncode == 0, result.stderr
    assert "/ 20 = 7.00" in result.stdout
    assert "Overall: 7.0 (Needs Attention)" in result.stdout


@pytest.mark.parametrize("scores,shown", [
    ("architecture=7.96,security=8.0", "Overall: 8.0 (Healthy)"),          # 7.98 shows as 8.0
    ("architecture=7.9,security=7.9", "Overall: 7.9 (Needs Attention)"),
    ("architecture=4.96,security=5.0", "Overall: 5.0 (Needs Attention)"),  # 4.98 shows as 5.0
])
def test_status_band_matches_the_score_as_shown(tmp_path, scores, shown):
    """The band is chosen from the one-decimal score a reader sees, never a hidden fraction."""
    result = run(resolver_file(tmp_path, two_domain_weights()), scores)
    assert result.returncode == 0, result.stderr
    assert shown in result.stdout


def test_critical_caps_the_overall_at_four(tmp_path):
    result = run(resolver_file(tmp_path, two_domain_weights()),
                 "architecture=9,security=9", "--critical")
    assert "capped at 4.0" in result.stdout
    assert "Overall: 4.0 (Critical)" in result.stdout


def test_weights_not_summing_to_100_are_refused(tmp_path):
    weights = {d: 5 for d in DOMAINS}
    result = run(resolver_file(tmp_path, weights), "architecture=9")
    assert result.returncode != 0
    assert "weights sum to 50" in result.stderr
