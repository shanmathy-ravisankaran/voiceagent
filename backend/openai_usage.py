import os


def get_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing or empty.")
    return api_key


def mask_api_key(api_key: str) -> str:
    if len(api_key) <= 10:
        return "***"
    return f"{api_key[:7]}...{api_key[-4:]}"


def log_openai_usage(feature: str, api_name: str, model: str) -> str:
    api_key = get_openai_api_key()
    print(
        f"[openai] feature={feature} api={api_name} model={model} "
        f"key={mask_api_key(api_key)}"
    )
    return api_key
