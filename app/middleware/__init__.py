from flask import Flask

from .rate_limiting import init_rate_limiter, limiter
from .request_logger import log_request_middleware
from .security_headers import configure_security


def init_middleware(app: Flask) -> None:
    log_request_middleware(app)
    configure_security(app)
    init_rate_limiter(app)
