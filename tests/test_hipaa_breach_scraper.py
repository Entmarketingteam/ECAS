from unittest.mock import patch
from signals.hipaa_breach_scraper import (
    parse_breach_csv, extract_export_form, select_recent_breaches, run_hipaa_outbound_pipeline
)


@patch("signals.hipaa_breach_scraper.SeenTracker")
@patch("signals.hipaa_breach_scraper.route_lead_to_n8n")
@patch("signals.hipaa_breach_scraper.verify_email_cascade")
@patch("signals.hipaa_breach_scraper.find_contacts_for_domain")
@patch("signals.hipaa_breach_scraper.resolve_domain")
@patch("signals.hipaa_breach_scraper.fetch_active_hipaa_breaches")
def test_pipeline_routes_verified_lead_with_sector(
    mock_fetch, mock_resolve, mock_find, mock_verify, mock_route, mock_seen
):
    mock_fetch.return_value = [{
        "company_name": "Acme Health", "state": "TN", "breach_type": "Hacking/IT Incident",
        "individuals_affected": "1807", "breach_date": "05/22/2026",
    }]
    mock_seen.return_value.is_seen.return_value = False
    mock_resolve.return_value = "acmehealth.com"
    mock_find.return_value = [{"email": "cco@acmehealth.com", "first_name": "A", "last_name": "B", "title": "CCO"}]
    mock_verify.return_value = ("verified_clean", "million_verifier")

    run_hipaa_outbound_pipeline()

    mock_route.assert_called_once()
    lead = mock_route.call_args[0][0]
    assert lead["sector"] == "Document Destruction & HIPAA Compliance"
    assert lead["custom_fields"]["affected_individuals"] == "1807"


@patch("signals.hipaa_breach_scraper.SeenTracker")
@patch("signals.hipaa_breach_scraper.route_lead_to_n8n")
@patch("signals.hipaa_breach_scraper.resolve_domain")
@patch("signals.hipaa_breach_scraper.fetch_active_hipaa_breaches")
def test_pipeline_filters_under_500_affected(mock_fetch, mock_resolve, mock_route, mock_seen):
    mock_fetch.return_value = [{
        "company_name": "Tiny Clinic", "state": "TN", "breach_type": "x",
        "individuals_affected": "12", "breach_date": "05/22/2026",
    }]
    mock_seen.return_value.is_seen.return_value = False
    run_hipaa_outbound_pipeline()
    mock_resolve.assert_not_called()  # filtered before domain resolution
    mock_route.assert_not_called()


def test_select_recent_returns_freshest_first_capped():
    cases = [
        {"company_name": "old", "breach_date": "01/05/2026"},
        {"company_name": "new", "breach_date": "06/02/2026"},
        {"company_name": "mid", "breach_date": "03/10/2026"},
    ]
    out = select_recent_breaches(cases, 2)
    assert [c["company_name"] for c in out] == ["new", "mid"]


def test_select_recent_caps_at_n():
    cases = [{"company_name": str(i), "breach_date": "01/01/2026"} for i in range(50)]
    assert len(select_recent_breaches(cases, 25)) == 25


def test_select_recent_tolerates_bad_dates():
    cases = [
        {"company_name": "good", "breach_date": "06/02/2026"},
        {"company_name": "bad", "breach_date": ""},
    ]
    out = select_recent_breaches(cases, 5)
    assert out[0]["company_name"] == "good"  # bad date sorts last, good survives
    assert len(out) == 2

# Row 0 is PrimeFaces junk (UIPanel artifacts), not real headers -> parse positionally.
HEADER = '"javax.faces.component.UIPanel@1","javax.faces.component.UIPanel@2","c","d","e","f","g","h","i"'
ROW1 = '"JASON R EGBERT OD PC  ","WA","Healthcare Provider","1225","06/02/2026","Hacking/IT Incident","Network Server","Yes",""'
ROW2 = '"Acadia Healthcare Company, Inc","TN","Business Associate","1807","05/22/2026","Hacking/IT Incident","Email","Yes",""'


def test_parses_positional_rows_skipping_junk_header():
    csv_text = "\r\n".join([HEADER, ROW1, ROW2]) + "\r\n"
    out = parse_breach_csv(csv_text)
    assert len(out) == 2


def test_field_mapping_and_strips_whitespace():
    csv_text = "\r\n".join([HEADER, ROW1]) + "\r\n"
    rec = parse_breach_csv(csv_text)[0]
    assert rec == {
        "company_name": "JASON R EGBERT OD PC",  # trailing spaces stripped
        "state": "WA",
        "breach_type": "Hacking/IT Incident",
        "individuals_affected": "1225",
        "breach_date": "06/02/2026",
    }


def test_empty_returns_empty():
    assert parse_breach_csv("") == []
    assert parse_breach_csv(HEADER + "\r\n") == []


def test_extract_export_form_pulls_runtime_ids():
    # The CSV export button id (j_idtNNN) is an auto-generated Mojarra id that
    # shifts on redeploy; it must be read from the page HTML, never hardcoded.
    # The real command source lives in the anchor's jsfcljs map (j_idt384) — NOT
    # the <img> id sitting on csv.png (j_idt385). Posting the img id silently
    # returns 200+HTML. Mirror the real HHS markup exactly.
    html = (
        '<form id="ocrForm" name="ocrForm">'
        '<input type="hidden" name="javax.faces.ViewState" id="x" value="VS-TOKEN-123" />'
        '<a href="#" onclick="mojarra.jsfcljs(document.getElementById(\'ocrForm\'),'
        "{'ocrForm:j_idt384':'ocrForm:j_idt384'},'');return false\">"
        '<img id="ocrForm:j_idt385" src="/ocr/images/icons/csv.png?pfdrid_c=true" alt="CSV" />'
        '</a></form>'
    )
    form = extract_export_form(html)
    assert form["viewstate"] == "VS-TOKEN-123"
    # the command source from jsfcljs, not the img id
    assert form["csv_button_id"] == "ocrForm:j_idt384"
