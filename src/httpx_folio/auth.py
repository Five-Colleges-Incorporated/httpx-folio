"""FOLIO Authentication Schemes."""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, NamedTuple

import httpx

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator


@dataclass(frozen=True)
class FolioParams:
    """Connection parameters for FOLIO.

    base_url and auth_tenant can be found in Settings > Software versions.
    """

    """The service url for FOLIO."""
    base_url: str
    """The FOLIO tenant used for authentication.

    ECS setups are not currently supported, but the name auth_tenant has been
    chosen for future compatibility with ECS."""
    auth_tenant: str
    """The service user with permissions to query FOLIO."""
    username: str
    """The service user's FOLIO password."""
    password: str


class RefreshTokenAuth(httpx.Auth):
    """Implements FOLIO's refresh token auth scheme.

    Eureka and Okapi backends are supported by this scheme.
    """

    class _Token(NamedTuple):
        value: str

    def __init__(self, params: FolioParams):
        """Initializes the Authentication method with an access token."""
        self._params = params
        self._token = RefreshTokenAuth._do_auth(self._params)

    def auth_flow(
        self,
        request: httpx.Request,
    ) -> Generator[httpx.Request, httpx.Response, None]:
        """Override the default auth_flow to manage FOLIO token headers and refresh."""
        t = self._token.value
        request.headers["x-okapi-token"] = t
        response = yield request

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            self._token = RefreshTokenAuth._do_auth(self._params)
            t = self._token.value
            request.headers["x-okapi-token"] = t
            yield request

    async def async_auth_flow(
        self,
        request: httpx.Request,
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        """Override the default async_auth_flow to block unsupported usage."""
        sync_msg = "Cannot use a sync authentication class with httpx.AsyncClient"
        raise RuntimeError(sync_msg)
        yield request  # Unreachable but makes type checking happier

    @staticmethod
    def _do_auth(params: FolioParams) -> RefreshTokenAuth._Token:
        res = httpx.post(
            params.base_url.rstrip("/") + "/authn/login-with-expiry",
            headers={"x-okapi-tenant": params.auth_tenant},
            json={
                "username": params.username,
                "password": params.password,
            },
        )
        res.raise_for_status()

        return RefreshTokenAuth._Token(
            res.cookies["folioAccessToken"],
        )
