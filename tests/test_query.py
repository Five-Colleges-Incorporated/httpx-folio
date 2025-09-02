from __future__ import annotations

from dataclasses import dataclass

import httpx
from pytest_cases import parametrize, parametrize_with_cases

from httpx_folio.query import DEFAULT_PAGE_SIZE, QueryType


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
    expected: httpx.QueryParams

    query: QueryType | None = None
    limit: int | None = None


class NormalizedCases:
    def case_default(self) -> NormalizedCase:
        return NormalizedCase(
            expected=httpx.QueryParams(
                "query=cql.allRecords=1"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true",
            ),
        )

    def case_largepage(self) -> NormalizedCase:
        return NormalizedCase(
            limit=10000,
            expected=httpx.QueryParams(
                "query=cql.allRecords=1&limit=10000&perPage=10000&stats=true",
            ),
        )

    def case_simple_query(self) -> NormalizedCase:
        return NormalizedCase(
            query="simple query",
            expected=httpx.QueryParams(
                "query=simple query&filters=simple query"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true",
            ),
        )

    def case_cql_str(self) -> NormalizedCase:
        return NormalizedCase(
            query="simple query sortBy index",
            expected=httpx.QueryParams(
                f"query=simple query sortBy index&limit={DEFAULT_PAGE_SIZE}",
            ),
        )

    @parametrize(
        query=[
            {"query": "simple query"},
            httpx.QueryParams({"query": "simple query"}),
        ],
    )
    def case_cql_params(self, query: QueryType) -> NormalizedCase:
        return NormalizedCase(
            query=query,
            expected=httpx.QueryParams(
                f"query=simple query&limit={DEFAULT_PAGE_SIZE}",
            ),
        )

    @parametrize(
        query=[
            {"filters": "one filter"},
            httpx.QueryParams({"filters": "one filter"}),
        ],
    )
    def case_erm_one_filter(
        self,
        query: QueryType,
    ) -> NormalizedCase:
        return NormalizedCase(
            query=query,
            expected=httpx.QueryParams(
                f"filters=one filter&perPage={DEFAULT_PAGE_SIZE}&stats=true",
            ),
        )

    @parametrize(
        query=[
            {"filters": ["two", "filters"]},
            httpx.QueryParams({"filters": ["two", "filters"]}),
        ],
    )
    def case_erm_multiple_filter(
        self,
        query: QueryType,
    ) -> NormalizedCase:
        return NormalizedCase(
            query=query,
            expected=httpx.QueryParams(
                f"filters=two&filters=filters&perPage={DEFAULT_PAGE_SIZE}&stats=true",
            ),
        )


@parametrize_with_cases("tc", cases=NormalizedCases)
def test_normalized(tc: NormalizedCase) -> None:
    from httpx_folio.query import QueryParams as uut

    actual = (
        uut(tc.query) if tc.limit is None else uut(tc.query, tc.limit)
    ).normalized()

    assert actual == tc.expected
