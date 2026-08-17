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


def get_openai_judge_model() -> str:
    """Return the model used only for post-generation semantic grading."""

    model = os.getenv("OPENAI_JUDGE_MODEL")
    if not model:
        raise ConfigurationError(
            "OPENAI_JUDGE_MODEL environment variable is not configured"
        )
    return model
