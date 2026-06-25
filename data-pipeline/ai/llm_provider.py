"""Provider-neutral LangChain chat model factory with ordered failover."""

from __future__ import annotations

import os


PROVIDER_DEFAULT_MODELS = {
    "openrouter": "nvidia/nemotron-nano-9b-v2:free",
    "mistral": "mistral-small-latest",
    "cerebras": "gpt-oss-120b",
    "groq": "llama-3.1-8b-instant",
}

PROVIDER_KEY_ENVS = {
    "openrouter": "OPENROUTER_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "cerebras": "CEREBRAS_API_KEY",
    "groq": "GROQ_API_KEY",
}


def get_provider_chain() -> list[tuple[str, str, str]]:
    """Return configured providers in failover order."""
    raw_chain = os.getenv("LLM_PROVIDER_CHAIN", "").strip()
    if raw_chain:
        providers = [item.strip().lower() for item in raw_chain.split(",") if item.strip()]
    else:
        providers = [
            os.getenv("LLM_PROVIDER", "groq").lower(),
            os.getenv("LLM_FALLBACK_PROVIDER", "groq").lower(),
        ]

    providers = list(dict.fromkeys(providers))
    chain = []
    for index, provider in enumerate(providers):
        model = os.getenv(
            f"{provider.upper()}_MODEL",
            PROVIDER_DEFAULT_MODELS.get(provider, ""),
        )
        if not raw_chain:
            if index == 0:
                model = os.getenv("LLM_MODEL", model)
            elif index == 1:
                model = os.getenv("LLM_FALLBACK_MODEL", model)

        key_env = PROVIDER_KEY_ENVS.get(provider, "")
        api_key = os.getenv(key_env, "") if key_env else ""
        if provider == "groq" and index > 0:
            api_key = os.getenv("GROQ_FALLBACK_API_KEY", "") or api_key
        chain.append((provider, model, api_key))
    return chain


def get_provider_config(
    fallback: bool = False,
    provider_index: int | None = None,
) -> tuple[str, str, str]:
    """Return one provider config; compatible with the old two-slot API."""
    chain = get_provider_chain()
    index = provider_index if provider_index is not None else (1 if fallback else 0)
    if index < 0 or index >= len(chain):
        return "", "", ""
    return chain[index]


def create_chat_model(
    *,
    fallback: bool = False,
    provider_index: int | None = None,
    temperature: float = 0.2,
    max_tokens: int = 1024,
):
    provider, model, api_key = get_provider_config(
        fallback=fallback,
        provider_index=provider_index,
    )
    if not provider:
        raise RuntimeError("No LLM provider is configured for this failover slot")
    if not api_key:
        raise RuntimeError(f"API key is not configured for LLM provider '{provider}'")
    if not model:
        raise RuntimeError(f"LLM model is not configured for provider '{provider}'")

    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=model,
            temperature=temperature,
            api_key=api_key,
            max_tokens=max_tokens,
        )

    from langchain_openai import ChatOpenAI

    provider_options = {
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "default_headers": {
                "HTTP-Referer": "http://localhost:5173",
                "X-OpenRouter-Title": "TechJob AI",
            },
        },
        "mistral": {"base_url": "https://api.mistral.ai/v1"},
        "cerebras": {"base_url": "https://api.cerebras.ai/v1"},
    }
    options = provider_options.get(provider)
    if options is None:
        raise RuntimeError(f"Unsupported LLM provider: {provider}")

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        **options,
    )
