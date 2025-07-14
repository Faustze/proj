from flask import Flask
from flask_cors import CORS

from .hooks import init_hooks
from .middleware import init_middleware


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    init_middleware(app)
    init_hooks(app)

    from app.views import auth_bp, main_bp, task_bp, user_bp

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # print("\nRegistered Endpoints:")
    # for rule in app.url_map.iter_rules():
    #     methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
    #     print(f"{rule.endpoint:30s} [{methods}] → {rule.rule}")
    # print()

    return app
