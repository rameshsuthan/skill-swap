"""Browser-test entry point; controlled model is never selectable in production."""
from skillswap.api import create_app
from fake_model import ControlledModel
app=create_app(model=ControlledModel())
