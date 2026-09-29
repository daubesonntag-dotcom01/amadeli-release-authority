from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "authority"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SOURCE_REPO = "daubesonntag-dotcom01/amadeli-os-canonical"

current = json.loads((AUTH / "current-integration.json").read_text())
assert current["schema"] == "amadeli.integration-authority.v1"
assert current["source_repo"] == SOURCE_REPO
assert current["branch"] == "t15-integration"
assert current["status"] == "CANONICAL"
assert SHA_RE.fullmatch(current["approved_sha"])

seen_prs: set[int] = set()

candidates = AUTH / "candidates"
if candidates.exists():
    for path in sorted(candidates.glob("pr-*.json")):
        row = json.loads(path.read_text())

        assert row["schema"] == "amadeli.integration-candidate.v1"
        assert row["source_repo"] == SOURCE_REPO

        pr = row["source_pr"]
        assert isinstance(pr, int) and pr > 0
        assert pr not in seen_prs
        seen_prs.add(pr)

        assert row["base_branch"] == "t15-integration"
        assert SHA_RE.fullmatch(row["base_sha"])
        assert SHA_RE.fullmatch(row["head_sha"])
        assert row["head_sha"] != row["base_sha"]

        # A candidate is admissible only when it was built against the
        # currently recognized canonical integration SHA.
        assert row["base_sha"] == current["approved_sha"]

        assert row["status"] == "APPROVED_FOR_MERGE"

        required = row["required_checks"]
        assert required == {
            "T15 data-driven PR policy and evidence": "success",
            "record-approval": "success",
        }

        run_id = row["t15_guard_run_id"]
        assert isinstance(run_id, int) and run_id > 0

print(
    f"AUTHORITY_VALIDATION_PASS "
    f"current={current['approved_sha']} "
    f"candidates={len(seen_prs)}"
)
