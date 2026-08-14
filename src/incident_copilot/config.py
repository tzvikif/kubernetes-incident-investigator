import os


class ConfigurationError(RuntimeError):
    """Raised when required application configuration is missing."""


def get_openai_model() -> str:
    model = os.getenv("OPENAI_MODEL")

    if not model:
        raise ConfigurationError(
            "OPENAI_MODEL environment variable is not configured"
        )

    return model