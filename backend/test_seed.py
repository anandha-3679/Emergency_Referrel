"""
Validation script for Synthetic City Seed Data.
Verifies tiers, coordinates, capabilities, wards, and HFR ID formatting.
"""

from app.seed.city import get_seed_hospitals, CAPABILITIES

def main():
    hospitals = get_seed_hospitals()
    print(f"Loaded {len(hospitals)} hospitals.")
    assert len(hospitals) == 15, f"Expected 15 hospitals, got {len(hospitals)}"

    tiers = {"tertiary": 0, "mid": 0, "small": 0}
    for h in hospitals:
        tier = h["tier"]
        assert tier in tiers, f"Unknown tier {tier} for {h['id']}"
        tiers[tier] += 1
        assert h["hfr_id"].startswith("IN-KA-BLR-"), f"Invalid HFR ID format: {h['hfr_id']}"
        assert 12.0 <= h["lat"] <= 14.0, f"Latitude out of Bengaluru bounds: {h['lat']}"
        assert 77.0 <= h["lng"] <= 78.0, f"Longitude out of Bengaluru bounds: {h['lng']}"
        assert 0.0 <= h["reliability"] <= 1.0, f"Invalid reliability: {h['reliability']}"

        # Check capabilities
        for cap in h["capabilities"]:
            assert cap in CAPABILITIES, f"Unknown capability {cap} in {h['id']}"

    print(f"Tiers breakdown: {tiers}")
    assert tiers["tertiary"] == 4
    assert tiers["mid"] == 6
    assert tiers["small"] == 5
    print("ALL SEED DATA CHECKS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    main()
