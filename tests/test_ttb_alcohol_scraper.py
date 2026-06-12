from signals.ttb_alcohol_scraper import parse_ttb_permits

HEADER = "Permit_Number,Owner_Name,Operating_Name,Street,City,State,Prem_Zip,Prem_County,Industry_Type"


def _row(*fields):
    # TTB serves all data records comma-joined on ONE physical line after the header.
    return ",".join(fields)


def test_parses_all_records_from_single_joined_line():
    # Two 9-col records concatenated on one line -> must yield 2, not 1.
    rec1 = ["AR-P-1", "LIQUID ARTISAN ALLIANCE LLC", "", "36642 N VASARI DR", "SCOTTSDALE", "AR", "85262", "", "Wholesaler (Alcohol)"]
    rec2 = ["WA-P-2", "COHO DISTRIBUTING LLC", "Columbia Distributing", "2310 SW 93RD AVE", "TUMWATER", "WA", "98512", "THURSTON", "Wholesaler (Alcohol)"]
    csv_text = HEADER + "\r\n" + _row(*rec1, *rec2) + "\r\n"
    out = parse_ttb_permits(csv_text)
    assert len(out) == 2


def test_field_mapping_and_operating_name_fallback():
    rec1 = ["AR-P-1", "LIQUID ARTISAN ALLIANCE LLC", "", "ST", "SCOTTSDALE", "AR", "85262", "", "Wholesaler (Alcohol)"]
    rec2 = ["WA-P-2", "COHO DISTRIBUTING LLC", "Columbia Distributing", "ST", "TUMWATER", "WA", "98512", "THURSTON", "Distilled Spirits Plant"]
    csv_text = HEADER + "\r\n" + _row(*rec1, *rec2) + "\r\n"
    out = parse_ttb_permits(csv_text)
    # rec1: blank operating name -> fall back to owner name
    assert out[0] == {
        "company_name": "LIQUID ARTISAN ALLIANCE LLC",
        "permit_type": "Wholesaler (Alcohol)",
        "state": "AR",
        "city": "SCOTTSDALE",
        "permit_number": "AR-P-1",
    }
    # rec2: operating name present -> use it
    assert out[1]["company_name"] == "Columbia Distributing"
    assert out[1]["permit_type"] == "Distilled Spirits Plant"


def test_empty_or_headerless_returns_empty():
    assert parse_ttb_permits("") == []
    assert parse_ttb_permits(HEADER + "\r\n") == []


def test_skips_blank_company_records():
    rec = ["P-1", "", "", "ST", "CITY", "TX", "1", "", "Importer (Alcohol)"]
    csv_text = HEADER + "\r\n" + _row(*rec) + "\r\n"
    assert parse_ttb_permits(csv_text) == []
