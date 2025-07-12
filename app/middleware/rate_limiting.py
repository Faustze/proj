from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"],
    storage_uri="redis://localhost:6379",
)


def init_rate_limiter(app: Flask):
    limiter.init_app(app)
