from __future__ import annotations

from dataclasses import dataclass

from pytest_cases import parametrize_with_cases


@dataclass(frozen=True)
class IntegrationOkTestCase:
    endpoint: str
    query: str | None = None
    comp: str = "id"


class IntegrationOkTestCases:
    def case_nonerm_noquery(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase("/coursereserves/courses")

    def case_erm_noquery(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase("/erm/org")

    def case_nonerm_query(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase(
            "/coursereserves/courses",
            query='department.name = "German Studies"',
        )

    def case_erm_query(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase("/erm/org", query="name=~A")

    def case_calendars(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase(
            "/calendar/calendars",
            comp="startDate",
        )


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
            comp1 = j[next(iter(j.keys()))][-1][tc.comp]

            res = client.get(tc.endpoint, params=op.offset_paging(page=2))
            res.raise_for_status()
            j = res.json()
            comp2 = j[next(iter(j.keys()))][0][tc.comp]

            assert comp1 < comp2

            ip = uut(tc.query, limit=2)
            if ip.can_page_by_id(path=tc.endpoint):
                res = client.get(tc.endpoint, params=ip.id_paging())
                res.raise_for_status()
                j = res.json()
                comp1 = j[next(iter(j.keys()))][-1][tc.comp]

                res = client.get(tc.endpoint, params=ip.id_paging(last_id=comp1))
                res.raise_for_status()
                j = res.json()
                comp2 = j[next(iter(j.keys()))][0][tc.comp]

                assert comp1 < comp2
