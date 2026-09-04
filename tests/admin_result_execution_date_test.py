from pathlib import Path


root = Path(__file__).resolve().parents[1]
repository = (root / "server_store/result_repository.py").read_text(encoding="utf-8")
api = (root / "qianduan/server_api_example.py").read_text(encoding="utf-8")
frontend = (root / "qianduan/admin-reserve-results.js").read_text(encoding="utf-8")
html = (root / "qianduan/admin-reserve-results.html").read_text(encoding="utf-8")

assert repository.count("substr(COALESCE(NULLIF(r.started_at, ''), r.created_at), 1, 10) = ?") == 2
assert 'request.args.get("executionDate")' in api
assert 'params.set("executionDate", dom.date.value)' in frontend
assert 'dom.date.value = beijingToday()' in frontend
assert "抢座日期" in html
assert "抢到日期" not in html

print("admin result execution date filter passed")
