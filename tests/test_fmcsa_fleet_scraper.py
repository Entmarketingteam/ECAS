from signals.fmcsa_fleet_scraper import build_icp_where


def test_where_filters_power_units_band_and_active():
    w = build_icp_where(min_pu=5, max_pu=50)
    # power_units is stored as text in the census -> must cast to number
    assert "(power_units::number) >= 5" in w
    assert "(power_units::number) <= 50" in w
    # MUST exclude inactive carriers (42% of the raw band are status I)
    assert "status_code = 'A'" in w
    # interstate-only is the clean cold-email ICP
    assert "carrier_operation = 'A'" in w
    # US-only — interstate carriers include Canadian/Mexican carriers (phy_state ON etc.)
    assert "phy_country = 'US'" in w


def test_where_optional_state_filter():
    assert "phy_state" not in build_icp_where()
    w = build_icp_where(states=["TX", "VA"])
    assert "phy_state in ('TX', 'VA')" in w


def test_where_optional_recency_filter():
    assert "mcs150_date" not in build_icp_where()
    w = build_icp_where(since_date="20260501 0000")
    assert "mcs150_date > '20260501 0000'" in w


def test_where_clauses_joined_with_and():
    w = build_icp_where(min_pu=10, max_pu=20, states=["TX"], since_date="20260101 0000")
    # all conditions present, AND-joined (no dangling AND)
    assert " AND " in w
    assert not w.strip().endswith("AND")
    assert not w.strip().startswith("AND")
