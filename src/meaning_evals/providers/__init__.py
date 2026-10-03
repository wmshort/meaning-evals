"""Provider adapters behind one interface. Only the command line constructs them."""

from __future__ import annotations

from .anthropic_provider import AnthropicProvider
from .base import (
    KEY_VARIABLES,
    ClientSettings,
    Completion,
    CompletionRequest,
    Provider,
    ProviderName,
    read_keys,
)
from .google_provider import GoogleProvider
from .openai_provider import OpenAIProvider


def make_provider(name: ProviderName, api_key: str, settings: ClientSettings) -> Provider:
    """Construct the adapter for `name` around a real SDK client."""
    if name == "anthropic":
        return AnthropicProvider.from_key(api_key, settings)
    if name == "openai":
        return OpenAIProvider.from_key(api_key, settings)
    return GoogleProvider.from_key(api_key, settings)


# Eight public names: the interface (five), the key rule (two) and the factory. The concrete
# adapters stay importable from their modules for tests but are not part of this surface.
__all__ = [
    "KEY_VARIABLES",
    "ClientSettings",
    "Completion",
    "CompletionRequest",
    "Provider",
    "ProviderName",
    "make_provider",
    "read_keys",
]
