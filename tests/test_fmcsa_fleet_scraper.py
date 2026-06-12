from unittest.mock import patch
from signals.fmcsa_fleet_scraper import build_icp_where, run_fmcsa_discovery_pipeline


@patch("signals.fmcsa_fleet_scraper.SeenTracker")
@patch("signals.fmcsa_fleet_scraper.route_lead_to_n8n")
@patch("signals.fmcsa_fleet_scraper.verify_email_cascade")
@patch("signals.fmcsa_fleet_scraper.find_contacts_for_domain")
@patch("signals.fmcsa_fleet_scraper.resolve_domain")
@patch("signals.fmcsa_fleet_scraper.discover_icp_carriers")
def test_pipeline_routes_verified_lead_with_sector(
    mock_discover, mock_resolve, mock_find, mock_verify, mock_route, mock_seen
):
    mock_discover.return_value = [{
        "dot_number": "284720", "legal_name": "DDS DELIVERY INC", "dba_name": "",
        "power_units": "30", "phy_state": "TX",
    }]
    mock_seen.return_value.is_seen.return_value = False
    mock_resolve.return_value = "ddsdelivery.com"
    mock_find.return_value = [{"email": "owner@ddsdelivery.com", "first_name": "A", "last_name": "B", "title": "Owner"}]
    mock_verify.return_value = ("verified_clean", "million_verifier")

    run_fmcsa_discovery_pipeline()

    mock_route.assert_called_once()
    lead = mock_route.call_args[0][0]
    assert lead["sector"] == "Fleet Logistics & Pest Control"
    assert lead["custom_fields"]["dot_number"] == "284720"
    assert lead["custom_fields"]["truck_count"] == "30"
    mock_seen.return_value.mark_seen.assert_called_with("fmcsa_census::284720")


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
