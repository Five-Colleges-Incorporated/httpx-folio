from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pytest_cases import parametrize_with_cases


class TestIntegration:
    def test_ok(self) -> None:
        from httpx_folio.auth import FolioParams
        from httpx_folio.auth import RefreshTokenAuth as uut

        uut(
            FolioParams(
                "https://folio-etesting-snapshot-kong.ci.folio.org",
                "diku",
                "diku_admin",
                "admin",
            ),
        )

    @dataclass(frozen=True)
    class FolioConnectionCase:
        expected: type[Exception]
        index: int
        value: str

    class FolioConnectionCases:
        def case_url(self) -> "TestIntegration.FolioConnectionCase":
            return TestIntegration.FolioConnectionCase(
                expected=httpx.ConnectError,
                index=0,
                value="https://not.folio.fivecolleges.edu",
            )

        def case_tenant(self) -> "TestIntegration.FolioConnectionCase":
            return TestIntegration.FolioConnectionCase(
                expected=httpx.HTTPStatusError,
                index=1,
                value="not a tenant",
            )

        def case_user(self) -> "TestIntegration.FolioConnectionCase":
            return TestIntegration.FolioConnectionCase(
                expected=httpx.HTTPStatusError,
                index=2,
                value="not a user",
            )

        def case_password(self) -> "TestIntegration.FolioConnectionCase":
            return TestIntegration.FolioConnectionCase(
                expected=httpx.HTTPStatusError,
                index=3,
                value="not the password",
            )

    @parametrize_with_cases("tc", cases=FolioConnectionCases)
    def test_bad_folio_connection(
        self,
        tc: FolioConnectionCase,
    ) -> None:
        from httpx_folio.auth import FolioParams
        from httpx_folio.auth import RefreshTokenAuth as uut

        params = [
            "https://folio-etesting-snapshot-kong.ci.folio.org",
            "diku",
            "diku_admin",
            "admin",
        ]
        params = [*params[: tc.index], tc.value, *params[tc.index + 1 :]]
        with pytest.raises(tc.expected):
            uut(FolioParams(*params))


@patch("httpx_folio.auth.httpx.post")
def test_refreshes(auth_mock: MagicMock) -> None:
    from httpx_folio.auth import FolioParams, RefreshTokenAuth

    auth_mock.return_value.cookies.__getitem__.return_value = "token"

    uut = RefreshTokenAuth(
        FolioParams(
            "https://base_url/",
            "auth_tenant",
            "username",
            "password",
        ),
    )
    auth_mock.reset_mock()

    call_count = 0

    def mock_refresh(req: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        res = httpx.Response(401 if call_count % 5 == 0 else 200)
        res.request = req
        return res

    with httpx.Client(
        auth=uut,
        transport=httpx.MockTransport(handler=mock_refresh),
    ) as test_client:
        for _ in range(100):
            res = test_client.get("http://url")
            res.raise_for_status()

    # we're calling 100 times but there will be bonus calls because token refresh
    assert call_count > 100
    assert len(auth_mock.call_args_list) == (call_count - 100)

    expected_authn = "https://base_url/authn/login-with-expiry"
    expected_headers = {"x-okapi-tenant": "auth_tenant"}
    expected_creds = {"username": "username", "password": "password"}
    assert all(
        c[0][0] == expected_authn
        and c.kwargs["headers"] == expected_headers
        and c.kwargs["json"] == expected_creds
        for c in auth_mock.call_args_list
    )


@patch("httpx_folio.auth.httpx.post")
async def test_refreshes_async(auth_mock: MagicMock) -> None:
    from httpx_folio.auth import FolioParams, RefreshTokenAuth

    auth_mock.return_value.cookies.__getitem__.return_value = "token"

    uut = RefreshTokenAuth(
        FolioParams(
            "https://base_url/",
            "auth_tenant",
            "username",
            "password",
        ),
    )
    auth_mock.reset_mock()

    def mock_refresh(req: httpx.Request) -> httpx.Response:
        res = httpx.Response(401)
        res.request = req
        return res

    async with httpx.AsyncClient(
        auth=uut,
        transport=httpx.MockTransport(handler=mock_refresh),
    ) as test_client:
        with pytest.raises(RuntimeError):
            await test_client.get("http://url")
