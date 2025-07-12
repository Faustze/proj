from flask import Flask, request


def log_request_middleware(app: Flask) -> None:
    @app.before_request
    def log_request() -> None:
        print(f"[Request] {request.method} {request.path}")
