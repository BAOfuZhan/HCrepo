from pathlib import Path


root = Path(__file__).resolve().parents[1]
html = (root / "qianduan/admin-reserve-results.html").read_text()
js = (root / "qianduan/admin-reserve-results.js").read_text()
api = (root / "qianduan/server_api_example.py").read_text()

assert 'id="submitTimeMode"' in html
assert '<option value="A">模式 A</option>' in html
assert '<option value="C">模式 C</option>' in html
assert html.count('<option value="">学校默认</option>') >= 2
assert 'id="submitTimeTokenDate"' in html
assert '<option value="submit_date">提交日期</option>' in html
assert '<option value="today">当天日期</option>' in html
assert 'mode: dom.submitMode.value' in js
assert 'firstTokenDateMode: dom.submitTokenDate.value' in js
assert 'submitOffsetRangeMs: minText ? [Number(minText), Number(maxText)] : null' in js
assert 'id="submitTimePrefetchRange"' in html
assert 'prefetchText.split(/[,，]/).map(value => Number(value.trim()))' in js
assert 'preFetchTokenRangeMs: prefetchRange' in js
assert 'if prefetch_range is not None:' in api
assert 'next_config["pre_fetch_token_range_ms"] = prefetch_range' in api
assert 'requested_mode not in {"A", "C"}' in api
assert 'if explicit_mode in {"A", "C"}' in api
assert 'first_token_date_mode not in {"today", "submit_date"}' in api
assert '"modeOverride"' in api
assert '"firstTokenDateModeOverride"' in api

print("admin submit mode checks passed")
