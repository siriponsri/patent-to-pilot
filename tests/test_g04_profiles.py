import json
from pathlib import Path

from patent_to_pilot.core.models import OrganizationProfile

ROOT = Path(__file__).parents[1]


def test_three_profiles_are_distinct_and_provenance_bound():
    profiles = []
    for profile_id in ("fictional-profile-a", "fictional-profile-b", "fictional-profile-c"):
        base = ROOT / "methodology" / "organizations" / profile_id / "v1"
        profile = json.loads((base / "profile.json").read_text(encoding="utf-8"))
        policy = json.loads((base / "policy.json").read_text(encoding="utf-8"))
        source_map = json.loads((base / "source-map.json").read_text(encoding="utf-8"))
        assert profile["profile_id"] in {"PTP-FIC-ORG-A", "PTP-FIC-ORG-B", "PTP-FIC-ORG-C"}
        assert profile["profile_version"] == "1.0.0"
        assert policy["policy_version"] == "1.0.0"
        assert source_map["profile_id"] == profile["profile_id"]
        assert (base / "confirmation-queue.md").exists()
        assert profile["unknowns"]
        typed = OrganizationProfile.model_validate({**profile, "record_id": profile["profile_id"]})
        assert typed.profile_id == profile["profile_id"]
        profiles.append(profile)
    assert len({profile["profile_id"] for profile in profiles}) == 3
    assert len({json.dumps(profile["stipulations"], sort_keys=True) for profile in profiles}) == 3
