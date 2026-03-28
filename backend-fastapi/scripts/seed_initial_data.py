from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import app.models  # noqa: F401

from app.db.base import Base
from app.db.seed import seed_initial_data
from app.db.session import SessionLocal, engine


def main() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_initial_data(db)
        print("Datos iniciales creados correctamente.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
