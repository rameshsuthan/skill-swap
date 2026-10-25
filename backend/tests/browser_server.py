"""Browser-test entry point; controlled model is never selectable in production."""

from fake_model import ControlledModel
from skillswap.api import create_app

app = create_app(model=ControlledModel())
