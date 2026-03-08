from typing import Any, Callable, Dict, Iterable, Optional


class Rule:
    rule: str


class URLMap:
    def iter_rules(self) -> Iterable[Rule]: ...


class Blueprint:
    def __init__(self, name: str, import_name: str, url_prefix: str = ...) -> None: ...

    def route(self, path: str, methods: Optional[list[str]] = ...) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...


def jsonify(obj: Any) -> Any: ...


def render_template(name: str, **kwargs: Any) -> str: ...


class Request:
    headers: Dict[str, str]
    remote_addr: str
    json: Any
    method: str
    path: str
    args: Dict[str, Any]


request: Request


class Flask:
    def __init__(self, import_name: str, static_folder: Optional[str] = ..., template_folder: Optional[str] = ...) -> None: ...
    config: Dict[str, Any]
    url_map: URLMap
    logger: Any

    def register_blueprint(self, bp: Blueprint) -> None: ...
    def before_request(self, f: Callable[[], Any]) -> None: ...
    def after_request(self, f: Callable[[Any], Any]) -> None: ...

    def run(self, *args: Any, **kwargs: Any) -> None: ...
