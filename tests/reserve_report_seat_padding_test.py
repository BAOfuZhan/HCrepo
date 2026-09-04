import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server_store.report_reserve_results import classify_seat_source, normalize_seat, seat_values


assert normalize_seat("6") == "006"
assert normalize_seat("54") == "054"
assert normalize_seat("165") == "165"
assert seat_values(["6", "54", "165"]) == ["006", "054", "165"]
assert classify_seat_source("54", ["054"], ["055"]) == "primary"
assert classify_seat_source("55", ["054"], ["055"]) == "backup"
assert classify_seat_source("239", ["240"], []) == "backup"
assert classify_seat_source("56", ["054"], ["055"]) == "unknown"

print("reserve report seat padding passed")
