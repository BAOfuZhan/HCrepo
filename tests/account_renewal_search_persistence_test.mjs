import assert from "node:assert/strict";
import fs from "node:fs";

const source = fs.readFileSync("qianduan/admin-reserve-results.js", "utf8");
const html = fs.readFileSync("qianduan/admin-reserve-results.html", "utf8");

const finishAction = source.match(/async function finishVirtualUserAction\(\) \{([\s\S]*?)\n\}/)?.[1] || "";
assert.doesNotMatch(finishAction, /dom\.query\.value\s*=\s*""/);
assert.match(finishAction, /loadDashboard\(\{ force: true \}\)/);
assert.match(source, /setSearchQuery\(phone\);\s+await finishVirtualUserAction\(\);/);
assert.doesNotMatch(source, /dom\.query\.value\s*=\s*""/);
assert.match(source, /if \(wasVirtual\) \{\s+await finishVirtualUserAction\(\);/);
assert.match(source, /sessionStorage\.setItem\(SEARCH_QUERY_KEY, value\)/);
assert.match(html, /admin-reserve-results\.js\?v=20260902-default-today-1/);
assert.match(html, /id="openScheduleReadingZoneLookupBtn"/);
assert.match(source, /openReadingZoneLookup\("schedule"\)/);
assert.match(html, /id="clearQuickAddUserDraftBtn"/);
assert.match(source, /localStorage\.setItem\(ADD_USER_DRAFT_KEY/);
assert.match(source, /if \(data\.kvVerified !== true\)[^;]+;\s*clearQuickAddUserDraft\(false\)/);
assert.match(html, /<span>启动天数<\/span><strong id="renewalQuickActiveDays">0 天<\/strong>/);
assert.doesNotMatch(html, /<span>自动续费<\/span>/);
assert.match(source, /renewalActiveDays\.textContent = `\$\{row\.activeDays \|\| 0\} 天`/);
assert.match(html, /id="renewalQuickChannel"[^>]*aria-label="续费平台"/);
assert.match(source, /adminFetch\("\/api\/admin\/renewal-channel"/);
assert.match(source, /selectQuickRenewalChannel\(row\.purchaseChannel\)/);
assert.match(source, /row\.serverDiscoveredOn \|\| dateOnly\(row\.createdAt\) \|\| "-"/);
assert.match(source, /暂停至 \$\{escapeHtml\(pauseUntil\)\}/);
assert.match(source, /timeZone: "Asia\/Shanghai"/);
assert.match(html, /id="quickAddUserBtn"/);
assert.doesNotMatch(html, /id="quickAddUserBtn"[^>]*hidden/);
assert.match(html, /id="quickAddUserDialog" class="admin-submit-dialog admin-quick-dialog"/);
assert.match(html, /id="quickAddUserSchedule"/);
assert.doesNotMatch(html, /id="quickAddUserSchedule"[^>]*required/);
assert.match(html, /id="quickAddUserStatus"/);
assert.match(source, /正在验证并保存/);
assert.match(html, /id="openReadingZoneLookupBtn"/);
assert.match(source, /\/api\/admin\/school-reading-zones/);
assert.match(source, /readingZoneCache\.set\(schoolId, meta\)/);
assert.match(html, /id="quickAddUserMaxHours"/);
assert.match(source, /data\.kvVerified !== true/);
assert.match(source, /setSearchQuery\(data\.user\?\.phone \|\| newUserPhone\)/);
const replaceRoomId = source.match(/function replaceRoomIdLine\(text, roomId\) \{[\s\S]*?\n\}/)?.[0];
assert.ok(replaceRoomId);
const replaceRoomIdLine = Function(`${replaceRoomId}\nreturn replaceRoomIdLine;`)();
assert.equal(
  replaceRoomIdLine("自习室id:9928\n座位号:055\n时间段:08:00-22:00", "13484"),
  "自习室id:13484\n座位号:055\n时间段:08:00-22:00",
);
assert.match(html, /id="quickAddUserSchoolId"/);
assert.match(source, /adminFetch\("\/api\/admin\/user"/);
assert.match(source, /getAddUserScheduleEditor\(\)\?\.getValue\(\)/);
assert.match(source, /globalRanges = extractRanges\(globalLine\)/);

console.log("account and renewal search persistence passed");
