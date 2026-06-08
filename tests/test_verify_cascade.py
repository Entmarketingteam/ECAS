import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from tools.verify_cascade import verify_email_cascade, init_retry_db

def test_init_db():
    conn = init_retry_db(":memory:")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='queue'")
    assert cursor.fetchone() is not None

@patch("urllib.request.urlopen")
def test_verify_million_verifier_deliverable(mock_urlopen):
    # Pass 1: Million Verifier returns deliverable
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'{"result": "deliverable", "status": "ok"}'
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    status, source = verify_email_cascade("test@builders.com", mv_key="mv_key", fm_key="fm_key")
    assert status == "verified_clean"
    assert source == "million_verifier"

@patch("urllib.request.urlopen")
def test_verify_findymail_fallback_catchall(mock_urlopen):
    # Pass 1: Million Verifier returns catch_all -> triggers Findymail
    # Create mock response to return first MV (catch_all) then Findymail (deliverable)
    mock_mv_resp = MagicMock()
    mock_mv_resp.read.return_value = b'{"result": "catch_all", "status": "ok"}'
    
    mock_fm_resp = MagicMock()
    mock_fm_resp.read.return_value = b'{"status": "deliverable", "email": "test@builders.com"}'
    
    mock_urlopen.return_value.__enter__.side_effect = [mock_mv_resp, mock_fm_resp]

    status, source = verify_email_cascade("test@builders.com", mv_key="mv_key", fm_key="fm_key")
    assert status == "catch_all_verified"
    assert source == "findymail"
