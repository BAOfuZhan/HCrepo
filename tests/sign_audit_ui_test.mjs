import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const api = readFileSync(new URL("../qianduan/server_api_example.py", import.meta.url), "utf8");
const html = readFileSync(new URL("../qianduan/sign-collections.html", import.meta.url), "utf8");
const js = readFileSync(new URL("../qianduan/sign-collections.js", import.meta.url), "utf8");

assert.match(api, /\/api\/admin\/sign-audit/);
assert.match(api, /timedelta\(days=3\)/);
assert.match(api, /response_json/);
assert.match(api, /request_url/);
assert.match(api, /SELECT account FROM source_users/);
assert.match(html, /signAuditPanel/);
assert.match(html, /signUserSearch/);
assert.match(js, /data-audit-user/);
assert.match(js, /renderUserSearch/);
assert.match(js, /data-search-user/);
assert.match(js, /data-search-auto/);
assert.match(js, /data-search-action="collect"/);
assert.match(js, /data-search-action="delete"/);
assert.match(js, /curReserves/);
assert.match(js, /房间.*座位.*状态/);
assert.match(js, /beijingDateTime/);
assert.match(js, /请求 URL/);
assert.match(js, /登录账号/);
assert.match(js, /未生成签到任务/);
assert.match(js, /未执行 ·/);
assert.match(js, /签到任务：/);
assert.match(js, /登录手机号/);
assert.match(js, /item\.executedAt \? beijingDateTime\(item\.executedAt\) : "未执行"/);

console.log("sign audit UI wiring passed");
