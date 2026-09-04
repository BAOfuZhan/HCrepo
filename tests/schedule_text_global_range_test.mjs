import assert from "node:assert/strict";
import fs from "node:fs";

const source = fs.readFileSync("qianduan/admin-reserve-results.js", "utf8");
const days = source.match(/const SCHEDULE_DAYS = \[[\s\S]*?\n\];/)?.[0];
const splitter = source.match(/function splitScheduleRange\(start, end, maxHours\) \{[\s\S]*?\n\}/)?.[0];
const seatNormalizer = source.match(/function normalizeSeatNumber\(value\) \{[\s\S]*?\n\}/)?.[0];
const parser = source.match(/function scheduleTextToMapping\(text, originalMapping, maxHours = 0\) \{[\s\S]*?\n\}/)?.[0];
assert.ok(days && splitter && seatNormalizer && parser);
const parse = Function(`${days}\n${splitter}\n${seatNormalizer}\n${parser}\nreturn scheduleTextToMapping;`)();
const mapping = parse("自习室id:9928\n座位号:055\n时间段:8.30-22.00", []);

assert.equal(mapping.length, 7);
assert.deepEqual(mapping[0].times, ["08:30", "22:00"]);
assert.deepEqual(mapping.map((item) => item.daysofweek[0]), [
  "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]);
const segmented = parse("自习室id:9928\n座位号:055\n时间段:08:00-22:00", [], 4);
assert.deepEqual(segmented.slice(0, 4).map((item) => item.times), [
  ["08:00", "12:00"], ["12:00", "16:00"], ["16:00", "20:00"], ["20:00", "22:00"],
]);
const chinesePunctuation = parse(
  "自习室id:9928\n座位号:055\n时间段:9：30-12：00，14.00—22.00",
  [],
);
assert.deepEqual(chinesePunctuation.slice(0, 2).map((item) => item.times), [
  ["09:30", "12:00"], ["14:00", "22:00"],
]);
const fullwidthAndBackups = parse(
  "自习室id:9928\n座位号:055\n时间段:9：30－12：00\n备选座位:13501－300，13502-340",
  [],
);
assert.deepEqual(fullwidthAndBackups[0].times, ["09:30", "12:00"]);
assert.ok(fullwidthAndBackups.every((item) => item.backupSeats === "13501-300,13502-340"));
const preservedBackups = parse(
  "自习室id:9928\n座位号:055\n周一:9：30-12：00",
  [{ daysofweek: ["Monday"], backupSeats: "13503-350" }],
);
assert.equal(preservedBackups[0].backupSeats, "13503-350");

const paddedSeats = parse(
  "自习室id:9928\n座位号:1,22,333\n时间段:09:30-12:00\n备选座位:13501-2,13502-33",
  [],
);
assert.deepEqual(paddedSeats[0].seatid, ["001", "022", "333"]);
assert.equal(paddedSeats[0].backupSeats, "13501-002,13502-033");

console.log("global schedule time range mapping passed");
