from pathlib import Path


source = (Path(__file__).resolve().parents[1] / "qianduan/server_api_example.py").read_text()
login = source.split('@app.post("/api/login")', 1)[1].split('@app.post("/api/logout")', 1)[0]

assert login.count('return _json_error("未查到此手机号用户", 404)') == 2
assert 'if matched and not _password_matches' in login
assert 'return _json_error("密码错误", 401)' in login
assert 'return _json_error("手机号或密码错误", 401)' not in login

print("login error message check passed")
