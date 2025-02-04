__all__ = (
    "templates",
    "TEMPLATE_DIR",
)

from fastapi.templating import Jinja2Templates

from pathlib import Path

this_folder = Path(__file__).parent

TEMPLATE_DIR = this_folder / "templates"

templates = Jinja2Templates(directory=TEMPLATE_DIR)
