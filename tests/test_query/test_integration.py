from __future__ import annotations

from dataclasses import dataclass

from pytest_cases import parametrize_with_cases


@dataclass(frozen=True)
class IntegrationOkTestCase:
    endpoint: str
    query: str | None = None


class IntegrationOkTestCases:
    def case_nonerm_noquery(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase("/coursereserves/courses")

    def case_erm_noquery(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase("/erm/org")

    def case_nonerm_query(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase(
            "/coursereserves/courses",
            'department.name = "German Studies"',
        )

    def case_erm_query(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase("/erm/org", "name=~A")


class TestIntegration:
    @parametrize_with_cases("tc", cases=IntegrationOkTestCases)
    def test_ok(self, tc: IntegrationOkTestCase) -> None:
        from httpx_folio.factories import FolioParams
        from httpx_folio.factories import (
            default_client_factory as make_client_factory,
        )
        from httpx_folio.query import QueryParams as uut

        with make_client_factory(
            FolioParams(
                "https://folio-etesting-snapshot-kong.ci.folio.org",
                "diku",
                "diku_admin",
                "admin",
            ),
        )() as client:
            res = client.get(tc.endpoint, params=uut(tc.query).normalized())
            res.raise_for_status()

            j = res.json()
            assert j["totalRecords"] > 1

            res = client.get(tc.endpoint, params=uut(tc.query).stats())
            res.raise_for_status()

            j = res.json()
            assert j["totalRecords"] > 1
            assert len(j[next(iter(j.keys()))]) == 1

            op = uut(tc.query, limit=2)
            res = client.get(tc.endpoint, params=op.offset_paging())
            res.raise_for_status()
            j = res.json()
            id1 = j[next(iter(j.keys()))][-1]["id"]

            res = client.get(tc.endpoint, params=op.offset_paging(2))
            res.raise_for_status()
            j = res.json()
            id2 = j[next(iter(j.keys()))][0]["id"]

            assert id1 < id2

            ip = uut(tc.query, limit=2)
            res = client.get(tc.endpoint, params=ip.id_paging())
            res.raise_for_status()
            j = res.json()
            id1 = j[next(iter(j.keys()))][-1]["id"]

            res = client.get(tc.endpoint, params=ip.id_paging(last_id=id1))
            res.raise_for_status()
            j = res.json()
            id2 = j[next(iter(j.keys()))][0]["id"]

            assert id1 < id2
