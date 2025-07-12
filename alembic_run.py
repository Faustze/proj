import subprocess

from app import create_app
from app.database import seed_data


def main():
    print("Resetting DB via Alembic...")
    subprocess.run(["alembic", "downgrade", "base"])
    subprocess.run(["alembic", "upgrade", "head"])
    seed_data()

    app = create_app()
    app.run(debug=True)


if __name__ == "__main__":
    main()
