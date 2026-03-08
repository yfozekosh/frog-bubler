import sys
import os
import types

# Ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Minimal fake `flask` to allow importing route modules without installing Flask
fake_flask = types.ModuleType("flask")

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
        # lightweight logger to satisfy app._attach_handlers_to_flask
        import types as _types
        self.logger = _types.SimpleNamespace(handlers=[], setLevel=lambda lvl: None)
        self._before = []
        self._after = []
    def before_request(self, f):
        self._before.append(f)
        return f
    def after_request(self, f):
        self._after.append(f)
        return f
    def register_blueprint(self, bp):
        for r in getattr(bp, 'routes', []):
            self.url_map._rules.append(r)
    def run(self, *args, **kwargs):
        return None

def _jsonify(x):
    return x

def _render_template(name):
    return f"rendered:{name}"

# Attach to fake_flask
fake_flask.Flask = _Flask
fake_flask.Blueprint = _Blueprint
fake_flask.jsonify = _jsonify
fake_flask.render_template = _render_template
# minimal request object used by route modules during import
fake_flask.request = types.SimpleNamespace(headers={}, remote_addr='127.0.0.1')

# Insert fake flask into sys.modules before importing the app
sys.modules['flask'] = fake_flask

# Provide a minimal fake `tapo` package so tests can import app without the real dependency.
fake_tapo = types.ModuleType("tapo")
fake_tapo.ApiClient = lambda username, password: None
fake_requests = types.ModuleType("tapo.requests")
fake_requests.EnergyDataInterval = types.SimpleNamespace(Hourly=1, Daily=2)
sys.modules["tapo"] = fake_tapo
sys.modules["tapo.requests"] = fake_requests

# Provide minimal fake apscheduler modules used by scheduler import
fake_aps = types.ModuleType("apscheduler")
fake_sched = types.ModuleType("apscheduler.schedulers")
fake_background = types.ModuleType("apscheduler.schedulers.background")

class FakeScheduler:
    def start(self):
        return None
    def add_job(self, *a, **k):
        return None
    def remove_job(self, *a, **k):
        return None

fake_background.BackgroundScheduler = FakeScheduler
sys.modules["apscheduler"] = fake_aps
sys.modules["apscheduler.schedulers"] = fake_sched
sys.modules["apscheduler.schedulers.background"] = fake_background
sys.modules["apscheduler.triggers"] = types.ModuleType("apscheduler.triggers")
sys.modules["apscheduler.triggers.cron"] = types.ModuleType("apscheduler.triggers.cron")
sys.modules["apscheduler.triggers.cron"].CronTrigger = lambda **k: None

from app import create_app


def test_create_app_routes_exist():
    app = create_app()
    assert app is not None
    rules = {r.rule for r in app.url_map.iter_rules()}
    # basic route checks
    assert "/" in rules
    assert "/api/status/<plug_id>" in rules
    assert "/api/energy/day/<plug_id>" in rules
