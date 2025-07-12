from app import create_app
from app.database import drop_db, init_db, seed_data
from app.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    app = create_app()
    drop_db()
    init_db()
    seed_data()
    app.run(debug=True, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    logger.info("Starting app from DSN")
    main()
