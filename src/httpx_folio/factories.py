"""Factories for httpx clients configured for FOLIO."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import httpx
from httpx_retries import Retry, RetryTransport

from .auth import FolioParams, RefreshTokenAuth

__all__ = ["FolioParams"]


def _httpx_default_timeout() -> httpx._types.TimeoutTypes:
    return httpx.Timeout(timeout=5.0)


@dataclass(frozen=True)
class BasicClientOptions:
    """The most basic options for creating FOLIO client."""

    retries: int = 3
    timeout: httpx._types.TimeoutTypes = field(default_factory=_httpx_default_timeout)


class BasicClientFactory(Protocol):
    """Client factory for a single-tenant with default HTTPX options."""

    def __call__(self, o: BasicClientOptions = ..., /) -> httpx.Client:
        """Callable with or without BasicClientOptions."""
        ...


def default_client_factory(
    params: FolioParams,
) -> BasicClientFactory:
    """Factory method for creating a single tenant client with no customizations.

    Returns:
        A factory method for creating basic httpx Clients connected to FOLIO.

    Raises:
        httpx.HTTPError: When the provided params do not connect to FOLIO.

    Examples:
        from httpx_folio.factories import (
            FolioParams,
            default_client_factory as make_client_factory,
        )

        client_factory = make_client_factory(FolioParams(
            'https://folio-etesting-snapshot-kong.ci.folio.org',
            'diku',
            'diku_admin',
            'admin',
        ))
        with client_factory() as client:
            res = client.get(...)
            ...

    """
    auth = RefreshTokenAuth(params)

    def factory(o: BasicClientOptions | None = None) -> httpx.Client:
        o = o or BasicClientOptions()
        return httpx.Client(
            auth=auth,
            base_url=params.base_url,
            transport=RetryTransport(
                retry=Retry(
                    total=o.retries,
                    backoff_factor=0.5,
                ),
            ),
            timeout=o.timeout,
            headers={"x-okapi-tenant": params.auth_tenant},
        )

    return factory
