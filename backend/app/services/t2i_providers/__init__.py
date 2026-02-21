"""T2I (Text-to-Image) generation providers."""
from app.services.t2i_providers.base import BaseT2IProvider, T2IRequest, T2IResult
from app.services.t2i_providers.abstract_provider import AbstractProvider
from app.services.t2i_providers.flux_provider import FluxProvider
from app.services.t2i_providers.sd_provider import SDProvider

ALL_T2I_PROVIDERS: dict[str, BaseT2IProvider] = {
    "abstract": AbstractProvider(),
    "flux": FluxProvider(),
    "sd": SDProvider(),
}

__all__ = [
    "BaseT2IProvider",
    "T2IRequest",
    "T2IResult",
    "AbstractProvider",
    "FluxProvider",
    "SDProvider",
    "ALL_T2I_PROVIDERS",
]
