from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from server_store.renewal_repository import _cycle_start_for_school


user = {
    "schoolId": "001",
    "serverDiscoveredAt": "2026-08-31T23:59:59+08:00",
}

assert _cycle_start_for_school(None, user, None, date(2026, 9, 1)) == date(2026, 8, 31)

repository_source = (Path(__file__).resolve().parents[1] / "server_store/renewal_repository.py").read_text()
renewal_ui_source = (Path(__file__).resolve().parents[1] / "qianduan/renewal.js").read_text()
assert 'cycle_started_on = str(local_profile.get("cycleStartedOn") or suggested_cycle_started_on)' in repository_source
assert "normalizeDate(item.cycleCountStartedOn) || savedCycleStartedOn" in renewal_ui_source
print("renewal creation day start check passed")
