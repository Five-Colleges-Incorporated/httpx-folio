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
            assert len(j[next(iter(j.keys()))])


@dataclass(frozen=True)
class NormalizedCase:
    query: str | None = None
    expected_query: str = "cql.allRecords=1"
    expected_filters: str = ""

    expected_sort: str = "id;asc"

    limit: int | None = None
    expected_limit: str = "100"
    expected_perPage: str = "100"  # noqa: N815


class NormalizedCases:
    def case_default(self) -> NormalizedCase:
        return NormalizedCase()

    def case_largepage(self) -> NormalizedCase:
        return NormalizedCase(
            limit=10000,
            expected_limit="10000",
            expected_perPage="10000",
        )

    def case_simple_query(self) -> NormalizedCase:
        return NormalizedCase(
            query="simple query",
            expected_query="simple query",
            expected_filters="simple query",
        )


@parametrize_with_cases("tc", cases=NormalizedCases)
def test_normalized(tc: NormalizedCase) -> None:
    from httpx_folio.query import QueryParams as uut

    actual = (
        uut(tc.query) if tc.limit is None else uut(tc.query, tc.limit)
    ).normalized()
    assert actual["query"] == tc.expected_query
    assert actual["filters"] == tc.expected_filters
    assert actual["limit"] == tc.expected_limit
    assert actual["perPage"] == tc.expected_perPage
