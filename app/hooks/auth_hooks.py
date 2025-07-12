from flask import Flask, g, request


def register_auth_hooks(app: Flask) -> None:
    @app.before_request
    def check_auth() -> None:
        token: str | None = request.headers.get("Authorization")
        if token:
            g.current_user = token
