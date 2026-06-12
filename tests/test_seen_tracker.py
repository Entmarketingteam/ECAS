from tools.seen_tracker import SeenTracker


def test_new_key_is_not_seen(tmp_path):
    t = SeenTracker("ttb_leads_seen", db_path=tmp_path / "t.db")
    assert t.is_seen("ttb::abc") is False


def test_marked_key_is_seen(tmp_path):
    t = SeenTracker("ttb_leads_seen", db_path=tmp_path / "t.db")
    t.mark_seen("ttb::abc")
    assert t.is_seen("ttb::abc") is True


def test_mark_is_idempotent(tmp_path):
    t = SeenTracker("ttb_leads_seen", db_path=tmp_path / "t.db")
    t.mark_seen("ttb::abc")
    t.mark_seen("ttb::abc")  # must not raise on duplicate
    assert t.is_seen("ttb::abc") is True


def test_separate_tables_isolated(tmp_path):
    db = tmp_path / "t.db"
    a = SeenTracker("ttb_leads_seen", db_path=db)
    b = SeenTracker("fmcsa_leads_seen", db_path=db)
    a.mark_seen("k")
    assert b.is_seen("k") is False  # same db, different table -> isolated


def test_persists_across_instances(tmp_path):
    db = tmp_path / "t.db"
    SeenTracker("ttb_leads_seen", db_path=db).mark_seen("k")
    assert SeenTracker("ttb_leads_seen", db_path=db).is_seen("k") is True
