"""T2I (Text-to-Image) generation providers."""
from app.services.t2i_providers.base import (
    BaseT2IProvider,
    BaseCoverT2IProvider,
    T2IGenerationResult,
    T2IRequest,
    T2IResult,
)
from app.services.t2i_providers.abstract_provider import AbstractProvider
from app.services.t2i_providers.sd_provider import SDProvider

ALL_T2I_PROVIDERS: dict[str, BaseT2IProvider] = {
    "abstract": AbstractProvider(),
    "sd": SDProvider(),
}

__all__ = [
    "BaseT2IProvider",
    "BaseCoverT2IProvider",
    "T2IGenerationResult",
    "T2IRequest",
    "T2IResult",
    "AbstractProvider",
    "SDProvider",
    "ALL_T2I_PROVIDERS",
]
