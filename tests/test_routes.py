import sys
import os
import types
import asyncio

# Insert minimal shims for dependencies before importing app modules
fake_flask = types.ModuleType("flask")

# Ensure project root is on sys.path so `import app` works
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

class _Rule:
    def __init__(self, rule):
        self.rule = rule

class _URLMap:
    def __init__(self):
        self._rules = []
    def iter_rules(self):
        for r in self._rules:
            yield _Rule(r)

class _Blueprint:
    def __init__(self, name, import_name, url_prefix=''):
        self.name = name
        self.import_name = import_name
        self.url_prefix = url_prefix or ''
        self.routes = []
    def route(self, path, methods=None):
        def decorator(f):
            full = (self.url_prefix + path).replace('//','/')
            # record route for testing
            self.routes.append(full)
            return f
        return decorator

class _Flask:
    def __init__(self, name, static_folder=None, template_folder=None):
        self.name = name
        self.static_folder = static_folder
        self.template_folder = template_folder
        self.config = {}
        self.url_map = _URLMap()
    def register_blueprint(self, bp):
        for r in getattr(bp, 'routes', []):
            self.url_map._rules.append(r)
    def run(self, *args, **kwargs):
        return None

def _jsonify(x):
    return x

def _render_template(name):
    return f"rendered:{name}"

fake_flask.Flask = _Flask
fake_flask.Blueprint = _Blueprint
fake_flask.jsonify = _jsonify
fake_flask.render_template = _render_template
fake_flask.request = types.SimpleNamespace(headers={}, remote_addr='127.0.0.1', json=None)

sys.modules['flask'] = fake_flask

# fake tapo
fake_tapo = types.ModuleType("tapo")
fake_tapo.ApiClient = lambda username, password: None
fake_requests = types.ModuleType("tapo.requests")
fake_requests.EnergyDataInterval = types.SimpleNamespace(Hourly=1, Daily=2)
sys.modules["tapo"] = fake_tapo
sys.modules["tapo.requests"] = fake_requests

# fake apscheduler
fake_background = types.ModuleType("apscheduler.schedulers.background")
class FakeScheduler:
    def start(self):
        return None
    def add_job(self, *a, **k):
        return None
    def remove_job(self, *a, **k):
        return None
fake_background.BackgroundScheduler = FakeScheduler
sys.modules["apscheduler.schedulers.background"] = fake_background
sys.modules["apscheduler.triggers.cron"] = types.ModuleType("apscheduler.triggers.cron")
sys.modules["apscheduler.triggers.cron"].CronTrigger = lambda **k: None

# Now import modules under test
from app.routes import main as main_route
from app.routes import config as config_route
from app.routes import activity as activity_route
from app.routes import control as control_route
from app.routes import status as status_route
from app.routes import energy as energy_route
from app.routes import schedules as schedules_route
from app.storage import data_manager as dm


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        # no current loop: create one, run, close
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    elif loop.is_running():
        # running loop (unlikely in tests): delegate to asyncio.run
        return asyncio.run(coro)
    else:
        return loop.run_until_complete(coro)


def get_json(resp):
    # route handlers sometimes return (body, status)
    if isinstance(resp, tuple):
        return resp[0]
    return resp


def setup_tmp_files(tmp_path):
    dm.SCHEDULE_FILE = str(tmp_path / "schedules.json")
    dm.CONFIG_FILE = str(tmp_path / "config.json")
    dm.ACTIVITY_LOG_FILE = str(tmp_path / "activity.json")


class FakeDevice:
    def __init__(self, on=True, power=1.23, data=None):
        self._on = on
        self._power = power
        self._data = data or [100, 200]

    async def get_device_info(self):
        return types.SimpleNamespace(device_on=self._on)

    async def get_current_power(self):
        return types.SimpleNamespace(current_power=self._power)

    async def get_energy_data(self, interval=None, start_date=None):
        return types.SimpleNamespace(data=self._data)


def test_main_index():
    resp = main_route.index()
    assert isinstance(resp, str) and resp.startswith("rendered:")


def test_config_get_and_update(tmp_path):
    setup_tmp_files(tmp_path)
    # ensure default config
    cfg = config_route.get_config()
    assert isinstance(cfg, dict)
    # update via request.json
    fake_req = sys.modules['flask'].request
    fake_req.json = {"plug_names": {"1": "One"}}
    resp = config_route.update_config()
    assert resp["success"] is True


def test_activity_log_endpoints(tmp_path):
    setup_tmp_files(tmp_path)
    dm.save_activity_log([])
    # add an entry directly
    dm.add_activity_log("1", "on", source="test")
    resp = activity_route.get_activity_log("1")
    assert isinstance(resp, list)
    # clear logs
    res = activity_route.clear_activity_log("1")
    assert res["success"] is True


def test_control_status_energy_and_schedules(tmp_path, monkeypatch):
    setup_tmp_files(tmp_path)

    # monkeypatch device control functions to avoid real network calls
    async def fake_turn_on(plug_id, source="manual", device_info=None):
        dm.add_activity_log(plug_id, "on", source=source, device_info=device_info)

    async def fake_turn_off(plug_id, source="manual", device_info=None):
        dm.add_activity_log(plug_id, "off", source=source, device_info=device_info)

    # patch the names imported into the route module so the route uses our fakes
    monkeypatch.setattr(control_route, 'turn_on_plug', fake_turn_on)
    monkeypatch.setattr(control_route, 'turn_off_plug', fake_turn_off)

    # monkeypatch get_device to return fake device
    async def fake_get_device(plug_id, retries=3):
        return FakeDevice()

    # patch get_device where routes imported it
    monkeypatch.setattr(status_route, 'get_device', fake_get_device)
    monkeypatch.setattr(energy_route, 'get_device', fake_get_device)

    # control endpoints
    res_on = get_json(run_async(control_route.turn_on('1')))
    assert res_on["success"] is True
    res_off = get_json(run_async(control_route.turn_off('1')))
    assert res_off["success"] is True

    # status
    res_status = get_json(run_async(status_route.get_status('1')))
    assert res_status["success"] is True
    assert "is_on" in res_status

    # energy day/month
    res_day = get_json(run_async(energy_route.get_energy_day('1')))
    assert res_day["success"] is True
    assert isinstance(res_day["energy"], (int, float))

    res_month = get_json(run_async(energy_route.get_energy_month('1')))
    assert res_month["success"] is True

    # schedules: add, list, delete
    fake_req = sys.modules['flask'].request
    fake_req.json = {"action": "on", "hour": 1, "minute": 2}
    add_resp = schedules_route.add_schedule('1')
    assert add_resp["success"] is True
    schedules = schedules_route.get_schedules('1')
    assert isinstance(schedules, list) and len(schedules) >= 1
    sid = schedules[0]["id"]
    del_resp = schedules_route.delete_schedule('1', sid)
    assert del_resp["success"] is True
