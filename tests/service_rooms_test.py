from pathlib import Path


source = (Path(__file__).resolve().parents[1] / "qianduan/server_api_example.py").read_text()
rooms = source.split('@app.get("/api/me/service-rooms")', 1)[1].split(
    '@app.get("/<path:asset_path>")', 1
)[0]
assert "school_reading_zones" in rooms
assert "WHERE school_id = ?" in rooms
assert '"id": row["room_id"]' in rooms
assert '"currentRoomId": current_room_id' in rooms
assert '"currentSeatNumber": current_seat_number' in rooms

report = source.split('@app.post("/api/me/service-report")', 1)[1].split(
    '@app.get("/api/me/service-reports")', 1
)[0]
assert 'action == "修改座位"' in report
assert 'action == "退款"' in report
assert '"请填写购买平台"' in report
for field in ("schoolId", "roomId", "roomName", "seatNumber"):
    assert field in report
assert 'return _json_error("提交的就是当前座位，无需修改")' in report
assert '"isOriginalRoom": "是" if room_id == original_room_id else "否"' in report
for field in ("originalRoomId", "originalRoomName", "originalSeatNumber"):
    assert field in report

print("service rooms check passed")
