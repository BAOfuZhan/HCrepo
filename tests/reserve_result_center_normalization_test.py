import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server_store.result_repository import normalize_result_sources


record = normalize_result_sources(
    {
        "status": "backup_success",
        "primary_seat": "54",
        "final_seat": "054",
        "raw": {
            "github": {"runId": "1"},
            "time_slots": [
                {
                    "primarySeat": "54",
                    "backupSeat": "55",
                    "attemptSeat": "54",
                    "finalSeat": "054",
                    "source": "backup",
                    "result": "备选成功",
                    "success": True,
                }
            ]
        },
    }
)

assert record["status"] == "primary_success"
assert record["raw"]["time_slots"][0]["source"] == "primary"
assert record["raw"]["time_slots"][0]["result"] == "首抢成功"

one_digit = normalize_result_sources(
    {
        "status": "backup_success",
        "raw": {
            "github": {"runId": "one-digit"},
            "time_slots": [
                {
                    "primarySeat": "6",
                    "attemptSeat": "6",
                    "finalSeat": "006",
                    "source": "backup",
                    "success": True,
                }
            ],
        },
    }
)
assert one_digit["status"] == "primary_success"

dynamic_backup = normalize_result_sources(
    {
        "status": "backup_success",
        "raw": {
            "github": {"runId": "2"},
            "time_slots": [
                {
                    "primarySeat": "54",
                    "backupSeat": "",
                    "attemptSeat": "55",
                    "finalSeat": "055",
                    "source": "backup",
                    "success": True,
                }
            ]
        },
    }
)
assert dynamic_backup["status"] == "backup_success"

server_report = normalize_result_sources(
    {
        "status": "backup_success",
        "raw": {
            "time_slots": [
                {
                    "primarySeat": "54",
                    "attemptSeat": "54",
                    "finalSeat": "054",
                    "source": "backup",
                    "success": True,
                }
            ]
        },
    }
)
assert server_report["status"] == "backup_success"

partial = normalize_result_sources(
    {
        "status": "partial_success",
        "final_seat": "054",
        "raw": {
            "github": {},
            "time_slots": [
                {"primarySeat": "54", "attemptSeat": "54", "finalSeat": "054", "source": "backup", "success": True},
                {"primarySeat": "54", "attemptSeat": "54", "source": "primary", "success": False},
            ],
        },
    }
)
assert partial["status"] == "partial_success"
assert partial["backup_result"] == "skipped"
assert "1个时间段未成功" in partial["final_reason"]

print("result center source normalization passed")
