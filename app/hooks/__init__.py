from flask import Flask

from .auth_hooks import register_auth_hooks


def init_hooks(app: Flask) -> None:
    register_auth_hooks(app)
