import json
from app.storage import data_manager as dm


def test_save_and_load_schedules(tmp_path):
    # point data files to tmp paths
    dm.SCHEDULE_FILE = str(tmp_path / "schedules.json")
    schedules = [
        {"id": "s1", "plug_id": "1", "action": "on", "hour": 12, "minute": 34}
    ]
    dm.save_schedules(schedules)
    loaded = dm.load_schedules()
    assert loaded == schedules


def test_activity_log_write_and_read(tmp_path):
    dm.ACTIVITY_LOG_FILE = str(tmp_path / "activity.json")
    # ensure fresh
    dm.save_activity_log([])
    entry = dm.add_activity_log("1", "on", source="test", device_info="ci")
    logs = dm.load_activity_log()
    assert isinstance(logs, list)
    assert logs[0]["plug_id"] == "1"
    assert logs[0]["action"] == "on"
