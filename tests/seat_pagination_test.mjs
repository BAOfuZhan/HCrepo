import assert from "node:assert/strict";
import fs from "node:fs";

const api = fs.readFileSync(new URL("../qianduan/server_api_example.py", import.meta.url), "utf8");
const js = fs.readFileSync(new URL("../qianduan/seat.js", import.meta.url), "utf8");

assert.match(api, /page_items = items\[page_start:page_start \+ safe_page_size\]/);
assert.match(api, /"totalPages": total_pages/);
assert.match(js, /params\.set\("page",/);
assert.match(js, /data-seat-page=/);
assert.doesNotMatch(js, /params\.set\("limit", "3000"\)/);

console.log("seat pagination checks passed");
