from langchain_google_genai import ChatGoogleGenerativeAI


def make_model(settings):
    if settings.gemini_model != "gemini-3.8-flash":
        raise ValueError("model_substitution_disabled")
    if not settings.google_api_key.get_secret_value():
        raise ValueError("google_api_key_required")
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        api_key=settings.google_api_key.get_secret_value(),
        vertexai=False,
        temperature=0,
        max_retries=0,
        timeout=25,
    )


def error_code(exc):
    text = str(exc).lower()
    if "429" in text or "resource_exhausted" in text:
        return "quota_limited"
    if "503" in text or "unavailable" in text:
        return "provider_unavailable"
    if "401" in text or "403" in text:
        return "provider_access_denied"
    if isinstance(exc, TimeoutError):
        return "execution_timeout"
    return "execution_error"
