import logging
from .resource_manager import user_data_dir


def configure_logging():
    folder = user_data_dir() / "logs"; folder.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=folder / "desktop-pet.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
