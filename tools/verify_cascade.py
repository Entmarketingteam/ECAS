import json
import sqlite3
import urllib.request
import urllib.parse as up
from config import MILLIONVERIFIER_API_KEY, FINDYMAIL_API_KEY, SQLITE_QUEUE_PATH

def init_retry_db(db_path=SQLITE_QUEUE_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            email TEXT PRIMARY KEY,
            retry_count INTEGER DEFAULT 0,
            error_msg TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def verify_email_cascade(email: str, mv_key: str = MILLIONVERIFIER_API_KEY, fm_key: str = FINDYMAIL_API_KEY) -> tuple[str, str]:
    """
    Two-pass validation. 
    Returns: (verification_status, source)
    verification_status: 'verified_clean', 'catch_all_verified', 'bounced', 'needs_manual_review'
    source: 'million_verifier', 'findymail', 'failed'
    """
    if not email:
        return "needs_manual_review", "failed"

    # Pass 1: Million Verifier Bulk V2 ($0.00019/verify)
    if mv_key:
        try:
            url = f"https://api.millionverifier.com/bulk/v2/single?api_key={mv_key}&email={up.quote(email)}"
            req = urllib.request.Request(url, headers={"User-Agent": "ECAS-Cascade-Verifier/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                result = data.get("result")
                if result == "deliverable":
                    return "verified_clean", "million_verifier"
                elif result in ["undeliverable", "invalid"]:
                    return "bounced", "million_verifier"
                # Else: catch_all or risky -> Fallback to Findymail
        except Exception as e:
            print(f"[Warning] Million Verifier failed for {email}: {e}. Falling back to Findymail.")

    # Pass 2: Findymail Search/Verify Fallback ($0.01/verify)
    if fm_key:
        try:
            url = f"https://api.findymail.com/v1/verify?email={up.quote(email)}"
            req = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "Authorization": f"Bearer {fm_key}",
                    "User-Agent": "ECAS-Cascade-Verifier/1.0",
                    "Accept": "application/json"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                status = data.get("status")
                if status == "deliverable":
                    return "catch_all_verified", "findymail"
                elif status == "undeliverable":
                    return "bounced", "findymail"
        except Exception as e:
            print(f"[Error] Findymail verification failed for {email}: {e}")
            # Cache failed verifications in SQLite to process in background later
            try:
                conn = init_retry_db()
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO queue (email, error_msg) VALUES (?, ?)", (email, str(e)))
                conn.commit()
                conn.close()
            except Exception as dbe:
                print(f"[Error] Failed to buffer verifications: {dbe}")

    return "needs_manual_review", "failed"
