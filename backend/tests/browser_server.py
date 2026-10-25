"""Browser-test entry point; controlled model is never selectable in production."""

from fake_model import ControlledModel
from skillswap.api import create_app
from skillswap.settings import Settings
from skillswap.vendor_memory import MemoryService
from test_memory_scope import MemoryClient

settings = Settings(mem0_enabled=True, mem0_api_key="test", pinecone_enabled=False)
client = MemoryClient()
app = create_app(
    settings, model=ControlledModel(), memory=MemoryService(settings, client_factory=lambda: client)
)
