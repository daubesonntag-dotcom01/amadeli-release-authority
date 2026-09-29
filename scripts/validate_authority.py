from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "authority"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SOURCE_REPO = "daubesonntag-dotcom01/amadeli-os-canonical"

REQUIRED_SOURCE_CHECKS = {
    "T15 data-driven PR policy and evidence": "success",
    "record-approval": "success",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


current_path = AUTH / "current-integration.json"
current = load(current_path)
assert current["schema"] == "amadeli.integration-authority.v1"
assert current["source_repo"] == SOURCE_REPO
assert current["branch"] == "t15-integration"
assert current["status"] == "CANONICAL"
assert SHA_RE.fullmatch(current["approved_sha"])

previous = current.get("previous_canonical_sha")
if previous is not None:
    assert SHA_RE.fullmatch(previous)
    assert previous != current["approved_sha"]

seen_prs: set[int] = set()

candidates = AUTH / "candidates"
if candidates.exists():
    for path in sorted(candidates.glob("pr-*.json")):
        row = load(path)

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
        assert row["required_checks"] == REQUIRED_SOURCE_CHECKS

        run_id = row["t15_guard_run_id"]
        assert isinstance(run_id, int) and run_id > 0

        status = row["status"]
        assert status in {"APPROVED_FOR_MERGE", "MERGED"}

        if status == "APPROVED_FOR_MERGE":
            # Pending approvals are valid only against the currently
            # recognized canonical integration SHA.
            assert row["base_sha"] == current["approved_sha"]
        else:
            assert SHA_RE.fullmatch(row["merge_commit_sha"])
            recovery_pr = row.get("recovery_pr")
            if recovery_pr is not None:
                assert isinstance(recovery_pr, int) and recovery_pr > 0

recoveries = AUTH / "recoveries"
recovery_rows: dict[str, dict] = {}
if recoveries.exists():
    for path in sorted(recoveries.glob("pr-*.json")):
        row = load(path)
        rel = str(path.relative_to(ROOT))
        recovery_rows[rel] = row

        assert row["schema"] == "amadeli.integration-recovery.v1"
        assert row["source_repo"] == SOURCE_REPO
        assert row["base_branch"] == "t15-integration"
        assert row["status"] == "RECOVERED"

        for key in (
            "canonical_anchor_sha",
            "base_sha",
            "head_sha",
            "merge_commit_sha",
        ):
            assert SHA_RE.fullmatch(row[key])

        assert row["canonical_anchor_sha"] != row["merge_commit_sha"]
        assert row["required_checks"] == REQUIRED_SOURCE_CHECKS

        post = row["post_merge_checks"]
        assert post == {
            "T15 Integration Smoke": "success",
            "T15 Main-to-Integration Sync Guard": "success",
        }

        for key in (
            "t15_guard_run_id",
            "record_approval_run_id",
            "integration_smoke_run_id",
            "main_sync_guard_run_id",
        ):
            assert isinstance(row[key], int) and row[key] > 0

promoted_via = current.get("promoted_via")
if promoted_via is not None:
    assert promoted_via in recovery_rows, (
        f"current promoted_via does not resolve to a recovery record: {promoted_via}"
    )
    recovery = recovery_rows[promoted_via]
    assert recovery["merge_commit_sha"] == current["approved_sha"]
    assert recovery["canonical_anchor_sha"] == current["previous_canonical_sha"]

print(
    f"AUTHORITY_VALIDATION_PASS "
    f"current={current['approved_sha']} "
    f"candidates={len(seen_prs)} "
    f"recoveries={len(recovery_rows)}"
)
