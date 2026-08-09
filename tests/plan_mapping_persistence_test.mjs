import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const source = await readFile(new URL("../workers/tongyi/src/worker.js", import.meta.url), "utf8");

assert.match(source, /const PLAN_MAPPING_DRAFT_KEY_PREFIX = "plan_mapping_draft:"/);
assert.match(source, /phone: document\.getElementById\("plan_extract_phone"\)/);
assert.match(source, /password: document\.getElementById\("plan_extract_password"\)/);
assert.match(source, /username: document\.getElementById\("plan_extract_username"\)/);
assert.match(source, /text: getPlanExtractTextEditor\(\)/);
assert.match(source, /localStorage\.removeItem\(getPlanMappingDraftStorageKey\(\)\)/);
assert.match(source, /document\.getElementById\("plan_extract_output"\)/);
assert.match(source, /editor\.setValue\("自习室id:"\)/);
assert.match(source, /class="btn btn-danger" onclick="clearPlanMappingDraft\(\)">清空已保存内容<\/button>/);
assert.match(source, /showAddUser\(\{[\s\S]*?\}, \{ clearPlanMappingAfterSave: true \}\);\n    toast\("已生成新用户草稿"\);/);
assert.match(source, /if \(!userId && clearPlanMappingAfterUserSave\) \{\n        clearPlanMappingDraft\(\);/);
