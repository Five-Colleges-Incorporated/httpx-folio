class TestIntegration:
    def test_ok(self) -> None:
        from httpx_folio.factories import FolioParams
        from httpx_folio.factories import (
            default_client_factory as make_client_factory,
        )

        uut = make_client_factory(
            FolioParams(
                "https://folio-etesting-snapshot-kong.ci.folio.org",
                "diku",
                "diku_admin",
                "admin",
            ),
        )
        with uut() as client:
            res = client.get("/groups")
            res.raise_for_status()
            assert res.json()["totalRecords"] > 0
