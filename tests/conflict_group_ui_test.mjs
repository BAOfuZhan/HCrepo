import assert from "node:assert/strict";
import vm from "node:vm";
import worker from "../workers/tongyi/src/worker.js";

const response = await worker.fetch(
  new Request("https://example.test/"),
  {},
  { waitUntil() {} },
);
const html = await response.text();
const scriptMatch = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(scriptMatch, "admin client script should exist");

const app = { innerHTML: "" };
const storage = new Map();
const context = vm.createContext({
  console,
  Request,
  Response,
  URL,
  crypto,
  fetch,
  confirm: () => true,
  navigator: {},
  setTimeout,
  clearTimeout,
  setInterval: () => 0,
  clearInterval() {},
  localStorage: {
    getItem: key => storage.get(key) ?? null,
    setItem: (key, value) => storage.set(key, String(value)),
    removeItem: key => storage.delete(key),
  },
  document: {
    getElementById: id => id === "app" ? app : null,
    querySelectorAll: () => [],
  },
  window: {
    addEventListener() {},
  },
});
new vm.Script(scriptMatch[1]).runInContext(context);

const schools = [
  { id: "school-a", name: "学校 A", conflict_group: "2", trigger_time: "08:00", dispatch_target: "server_relay", server_url: "https://school-a.example.test/api" },
  { id: "school-b", name: "学校 B", conflict_group: "2", trigger_time: "09:00", repo: "owner/repo" },
  { id: "school-c", name: "学校 C", conflict_group: "other", trigger_time: "10:00" },
];
context.__schoolsJson = JSON.stringify(schools);
const sections = JSON.parse(vm.runInContext(`
  schools = JSON.parse(__schoolsJson);
  JSON.stringify(buildSchoolDisplaySections(schools));
`, context));
assert.equal(sections[0].key, "group:2");
assert.deepEqual(sections[0].schools.map(school => school.id), ["school-a", "school-b"]);
assert.equal(sections[1].key, "other");

const listHtml = vm.runInContext("renderSchoolList()", context);
assert.match(html, /\.school-list\{display:grid;grid-template-columns:repeat\(3,minmax\(0,1fr\)\)/);
assert.match(listHtml, /class="school-card conflict-group-total-card"/);
assert.match(listHtml, /2（总卡片）/);
assert.match(listHtml, /包含 2 所学校/);
assert.doesNotMatch(listHtml, /学校 ID:/);
assert.equal((listHtml.match(/class="conflict-group-school"/g) || []).length, 0);
assert.equal((listHtml.match(/class="school-section"/g) || []).length, 4);
assert.ok(listHtml.indexOf("2（总卡片）") < listHtml.indexOf("学校 A"));
assert.doesNotMatch(listHtml.slice(0, listHtml.indexOf("学校 A")), /正式开始:/);
assert.ok(listHtml.indexOf("学校 A") < listHtml.indexOf("学校 B"));
assert.equal((listHtml.match(/class="school-group-divider"/g) || []).length, 1);
assert.ok(listHtml.indexOf("学校 B") < listHtml.indexOf("school-group-divider"));
assert.ok(listHtml.indexOf("school-group-divider") < listHtml.indexOf("学校 C"));
assert.match(html, /\.school-group-divider\{grid-column:1\/-1;border-top:1px solid/);

const groupHtml = vm.runInContext(`
  currentConflictGroupKey = "group:2";
  currentConflictGroupSchools = schools.slice(0, 2);
  users = [{
    id: "user-a",
    phone: "17600000000",
    username: "测试用户",
    status: "active",
    schedule: {},
    __schoolId: "school-a",
    __schoolName: "学校 A",
    __school: schools[0]
  }];
  renderConflictGroupDetail();
`, context);
assert.match(groupHtml, /组内全部用户（1）/);
assert.match(groupHtml, /输入组内学校 ID/);
assert.match(groupHtml, /school-a/);
assert.match(groupHtml, /class="user-table-scroll"/);
assert.match(groupHtml, /class="user-table user-table-compact"/);
assert.match(groupHtml, /class="school-server-link" href="https:\/\/school-a\.example\.test\/admin\.html"[^>]*>school-a<\/a>/);
assert.match(html, /\.school-server-link\{color:#1677ff;[^}]*text-decoration:underline/);
assert.match(html, /\.user-table-compact \.actions\{flex-wrap:nowrap/);
assert.match(html, /\.user-table-compact \.pause-days-action\{flex:0 0 auto\}/);
assert.match(groupHtml, /pauseUserForDays\('user-a', 'school-a', 'school-a_user-a'\)/);
assert.doesNotMatch(groupHtml, /学校配置<\/span>/);
assert.doesNotMatch(html, /\.conflict-group-column\{/);

await vm.runInContext(`
  conflictGroupUsersCache.set("group:2", {
    cachedAt: Date.now(),
    users: [{
      id: "cached-user",
      phone: "17611111111",
      username: "缓存用户",
      status: "active",
      schedule: {},
      __schoolId: "school-a",
      __school: schools[0]
    }]
  });
  openConflictGroup("group:2");
`, context);
assert.match(app.innerHTML, /缓存用户/);
assert.equal(vm.runInContext("conflictGroupUsersLoading", context), false);

vm.runInContext("invalidateConflictGroupUsersCache()", context);
assert.equal(vm.runInContext("conflictGroupUsersCache.get('group:2').cachedAt", context), 0);
assert.equal(vm.runInContext("conflictGroupUsersCache.get('group:2').users[0].id", context), "cached-user");
