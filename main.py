from __future__ import annotations

from src.storage.database import initialize_database


def main() -> None:
    initialize_database()
    print("Explainable Proctoring System database initialized.")


if __name__ == "__main__":
    main()
