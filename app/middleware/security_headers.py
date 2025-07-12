from flask import Flask
from flask_talisman import Talisman


def configure_security(app: Flask) -> None:
    is_production = False

    Talisman(app, force_https=is_production)
