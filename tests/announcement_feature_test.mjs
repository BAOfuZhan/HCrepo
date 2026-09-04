import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = path => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");
const serviceHtml = read("qianduan/service.html");
const serviceJs = read("qianduan/service.js");
const reportsHtml = read("qianduan/service-reports.html");
const reportsJs = read("qianduan/service-audits.js");
const backend = read("qianduan/server_api_example.py");
const schema = read("server_store/schema.sql");

assert.match(schema, /CREATE TABLE IF NOT EXISTS site_announcements/);
assert.match(backend, /@app\.get\("\/api\/announcement"\)/);
assert.match(backend, /@app\.put\("\/api\/admin\/announcement"\)/);
assert.match(serviceHtml, /id="siteAnnouncement"[^>]*hidden/);
assert.match(serviceJs, /fetch\("\/api\/announcement"/);
assert.match(serviceJs, /if \(!content\) return/);
assert.match(serviceJs, /announcement\.hidden = !state\.loggedIn \|\|/);
assert.match(reportsHtml, /id="announcementForm"/);
assert.match(reportsJs, /fetch\("\/api\/admin\/announcement"/);

console.log("announcement feature check passed");
