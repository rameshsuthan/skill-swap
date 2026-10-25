import pytest
from skillswap.model_factory import make_model
from skillswap.settings import Settings


def test_explicitly_authorized_flash_lite_uses_exact_model():
    settings = Settings(
        _env_file=None, google_api_key="test-key", gemini_model="gemini-3.5-flash-lite"
    )
    model = make_model(settings)
    assert model.model == "gemini-3.5-flash-lite"
    assert model.vertexai is False
    assert model.max_retries == 0


def test_unapproved_model_is_rejected_instead_of_substituted():
    settings = Settings(_env_file=None, google_api_key="test-key", gemini_model="unapproved-model")
    with pytest.raises(ValueError, match="model_substitution_disabled"):
        make_model(settings)
