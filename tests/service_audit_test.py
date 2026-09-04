import json
import sqlite3
from datetime import datetime, timedelta, timezone


def test_service_audit_schema_and_retention(tmp_path):
    db = tmp_path / "audit.sqlite3"
    conn = sqlite3.connect(db)
    schema = open("server_store/schema.sql", encoding="utf-8").read()
    conn.executescript(schema)
    now = datetime.now(timezone(timedelta(hours=8)))
    rows = [
        ("13800000000", "u1", "001", "manual", "pending", "续费", '{"duration":"1个月"}', (now - timedelta(hours=73)).isoformat()),
        ("13900000000", "u2", "002", "automatic", "completed", "暂停或启动", '{"after":"paused"}', now.isoformat()),
    ]
    conn.executemany("INSERT INTO service_audits (phone,user_id,school_id,category,status,action,detail_json,created_at) VALUES (?,?,?,?,?,?,?,?)", rows)
    conn.execute("DELETE FROM service_audits WHERE created_at < ?", ((now - timedelta(days=3)).isoformat(),))
    kept = conn.execute("SELECT phone, category, detail_json FROM service_audits").fetchall()
    assert kept == [("13900000000", "automatic", '{"after":"paused"}')]
    assert json.loads(kept[0][2])["after"] == "paused"


def test_pending_report_replacement_key(tmp_path):
    db = tmp_path / "replace.sqlite3"
    conn = sqlite3.connect(db)
    conn.executescript(open("server_store/schema.sql", encoding="utf-8").read())
    base = ("13800000000", "u1", "001", "manual", "pending", "续费")
    conn.execute("INSERT INTO service_audits (phone,user_id,school_id,category,status,action,detail_json,created_at) VALUES (?,?,?,?,?,?,?,?)", (*base, '{"duration":"1个月"}', "2026-08-28T09:00:00+08:00"))
    conn.execute("DELETE FROM service_audits WHERE school_id=? AND user_id=? AND category='manual' AND status='pending' AND action=?", ("001", "u1", "续费"))
    conn.execute("INSERT INTO service_audits (phone,user_id,school_id,category,status,action,detail_json,created_at) VALUES (?,?,?,?,?,?,?,?)", (*base, '{"duration":"3个月"}', "2026-08-28T10:00:00+08:00"))
    rows = conn.execute("SELECT detail_json FROM service_audits WHERE status='pending'").fetchall()
    assert rows == [('{"duration":"3个月"}',)]
