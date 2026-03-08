"""
Flask application factory and blueprint registration.

This module creates and configures the Flask application with all routes.
"""

from flask import Flask, request
import logging
import time
import os
import uuid
import json

# Logging configuration from environment
_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_LOG_JSON = os.getenv("LOG_JSON", "false").lower() in ("1", "true", "yes")

# configure module-level logger
logger = logging.getLogger("bubler")
if not logger.handlers:
    handler = logging.StreamHandler()

    class JSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            # include common extras if present
            for k, v in getattr(record, "__dict__", {}).items():
                if k in ("msg", "args", "levelname", "levelno", "name", "msg", "pathname", "lineno", "exc_info", "exc_text", "stack_info"):
                    continue
                if k.startswith("_"):
                    continue
                try:
                    json.dumps({k: v})
                    payload[k] = v
                except Exception:
                    payload[k] = str(v)
            return json.dumps(payload)

    class TextFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            ts = self.formatTime(record)
            rid = getattr(record, "request_id", None)
            rid_part = f" request_id={rid}" if rid else ""
            return f"{ts} bubler | {record.levelname} | {record.getMessage()}{rid_part}"

    if _LOG_JSON:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())
    logger.addHandler(handler)

# set level from env
try:
    logger.setLevel(getattr(logging, _LOG_LEVEL))
except Exception:
    logger.setLevel(logging.INFO)


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            # import g lazily to avoid requiring it at module import time (test shims)
            from flask import g as _g

            record.request_id = getattr(_g, "request_id", None)
        except Exception:
            record.request_id = None
        return True

handler.addFilter(RequestIDFilter())

# helper to attach handlers to Flask and Werkzeug loggers
def _attach_handlers_to_flask(app: Flask) -> None:
    # make Flask's logger use our handlers
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)
    # also attach to werkzeug (HTTP access) logger so access logs flow through bubler
    werk = logging.getLogger("werkzeug")
    werk.handlers = logger.handlers
    werk.setLevel(logger.level)


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, static_folder="../static", template_folder="../templates")
    app.config["DEBUG"] = True

    # attach our logging handlers to flask/werkzeug
    _attach_handlers_to_flask(app)

    # Per-request logging: generate a request id and record start time
    try:
        @app.before_request
        def _before():
            rid = uuid.uuid4().hex
            try:
                g.request_id = rid
            except Exception:
                # g may not be present in test shims
                pass
            try:
                g._start_time = time.time()
            except Exception:
                pass
            logger.info("request.start %s %s", request.method, request.path)

        @app.after_request
        def _after(response):
            try:
                start = getattr(g, "_start_time", None)
            except Exception:
                start = None
            duration = (time.time() - start) if start else None
            msg = f"request.end {request.method} {request.path} {response.status_code}"
            if duration is not None:
                msg = f"{msg} duration={duration:.3f}s"
            # log at error level for 5xx
            if 500 <= response.status_code:
                logger.error(msg)
            elif 400 <= response.status_code:
                logger.warning(msg)
            else:
                logger.info(msg)
            return response
    except Exception:
        # some test shims for Flask do not implement before_request/after_request
        logger.debug("Flask test shim may not support before_request/after_request decorators")

    # Register blueprints
    from app.routes import activity, config, control, energy, main, schedules, status

    app.register_blueprint(status.bp)
    app.register_blueprint(energy.bp)
    app.register_blueprint(control.bp)
    app.register_blueprint(schedules.bp)
    app.register_blueprint(config.bp)
    app.register_blueprint(activity.bp)

    # Register main route
    app.register_blueprint(main.bp)

    return app
