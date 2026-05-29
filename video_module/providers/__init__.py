from .base import AvatarProvider
from .falai import FalAIProvider

PROVIDERS = {
    "falai": FalAIProvider,
}


def get_provider(name: str) -> AvatarProvider:
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS)}")
    return PROVIDERS[name]()
