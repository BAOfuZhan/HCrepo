from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_admin_create_user_username_is_optional():
    html = (ROOT / "qianduan/admin-reserve-results.html").read_text()
    backend = (ROOT / "qianduan/server_api_example.py").read_text()

    assert '<span>Username（选填）</span><input id="quickAddUserUsername">' in html
    assert "if not phone or not password:" in backend
    assert "if not phone or not password or not username:" not in backend
