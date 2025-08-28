from dataclasses import dataclass

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
