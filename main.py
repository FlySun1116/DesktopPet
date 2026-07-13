from app.application import run
from app.logging_config import configure_logging

if __name__ == "__main__":
    configure_logging()
    raise SystemExit(run())
