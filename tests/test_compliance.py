"""Tests for EU/CA compliance filter."""
from enrichment.compliance import filter_contacts_for_compliance


def test_drops_eu_contacts():
    contacts = [
        {"email": "a@us.com", "country": "US"},
        {"email": "b@de.com", "country": "Germany"},
        {"email": "c@fr.com", "country": "France"},
        {"email": "d@ca.com", "country": "Canada"},
        {"email": "e@nl.com", "country": "Netherlands"},
    ]
    filtered, dropped = filter_contacts_for_compliance(contacts)
    assert len(filtered) == 1
    assert filtered[0]["email"] == "a@us.com"
    assert len(dropped) == 4


def test_explicit_optin_allows_eu():
    contacts = [
        {"email": "a@de.com", "country": "Germany", "optin_verified": True},
    ]
    filtered, dropped = filter_contacts_for_compliance(contacts)
    assert len(filtered) == 1
    assert len(dropped) == 0


def test_unknown_country_is_permissive():
    contacts = [{"email": "a@example.com", "country": None}]
    filtered, dropped = filter_contacts_for_compliance(contacts)
    assert len(filtered) == 1
