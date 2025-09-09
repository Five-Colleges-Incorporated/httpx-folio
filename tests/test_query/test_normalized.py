from __future__ import annotations

from dataclasses import dataclass

import httpx
from pytest_cases import parametrize, parametrize_with_cases

from httpx_folio.query import DEFAULT_PAGE_SIZE, QueryType

from . import QueryParamCase


@dataclass(frozen=True)
class NormalizedCase(QueryParamCase):
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

    def case_additional_params(self) -> NormalizedCase:
        return NormalizedCase(
            query={"additional": "param1", "and": "param2"},
            expected=httpx.QueryParams(
                "query=cql.allRecords=1"
                "&additional=param1&and=param2"
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

    @parametrize(
        query=[
            "simple query sortby index",
            "simple query sortBy index",
            "simple query SORTBY index",
        ],
    )
    def case_cql_str(self, query: str) -> NormalizedCase:
        return NormalizedCase(
            query=query,
            expected=httpx.QueryParams(
                f"query={query}&limit={DEFAULT_PAGE_SIZE}",
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
            {"sort": "id;asc"},
            httpx.QueryParams({"sort": "id;asc"}),
        ],
    )
    def case_erm_params(
        self,
        query: QueryType,
    ) -> NormalizedCase:
        return NormalizedCase(
            query=query,
            expected=httpx.QueryParams(
                f"sort=id;asc&perPage={DEFAULT_PAGE_SIZE}&stats=true",
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
