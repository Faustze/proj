from flask import Blueprint

main_bp = Blueprint("main", __name__, url_prefix="/")


@main_bp.route('/', methods=['GET'])
def main() -> str:
    return 'Hello world'
