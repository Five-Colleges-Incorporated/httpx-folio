from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx
from pytest_cases import parametrize, parametrize_with_cases

from . import QueryParamCase

if TYPE_CHECKING:
    from httpx_folio.query import QueryType


@dataclass(frozen=True)
class StatsCase(QueryParamCase):
    query: QueryType | None = None


class StatsCases:
    def case_default(self) -> StatsCase:
        return StatsCase(
            expected=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id"
                "&sort=id;asc&limit=1&perPage=1"
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
    def case_sorted_cql(self, query: str) -> StatsCase:
        return StatsCase(
            query=query,
            expected=httpx.QueryParams(
                f"query={query}&limit=1",
            ),
        )

    @parametrize(
        query=[
            "simple query sortby index",
            "simple query sortBy index",
            "simple query SORTBY index",
        ],
    )
    def case_sorted_cql_dict(self, query: str) -> StatsCase:
        return StatsCase(
            query={"query": query},
            expected=httpx.QueryParams(
                f"query={query}&limit=1",
            ),
        )

    def case_add_sort_cql(self) -> StatsCase:
        return StatsCase(
            query={"query": "simple query"},
            expected=httpx.QueryParams(
                "query=simple query sortBy id&limit=1",
            ),
        )

    def case_add_sort(self) -> StatsCase:
        return StatsCase(
            query="simple query",
            expected=httpx.QueryParams(
                "query=simple query sortBy id&filters=simple query"
                "&sort=id;asc&limit=1&perPage=1"
                "&stats=true",
            ),
        )

    def case_add_sort_erm(self) -> StatsCase:
        return StatsCase(
            query={"filters": "simple query"},
            expected=httpx.QueryParams(
                "filters=simple query&sort=id;asc&perPage=1&stats=true",
            ),
        )

    def case_sorted_erm(self) -> StatsCase:
        return StatsCase(
            query={"filters": "simple query", "sort": "index;desc"},
            expected=httpx.QueryParams(
                "filters=simple query&sort=index;desc&perPage=1&stats=true",
            ),
        )


@parametrize_with_cases("tc", cases=StatsCases)
def test_stats(tc: StatsCase) -> None:
    from httpx_folio.query import QueryParams as uut

    actual = uut(tc.query, 1000).stats()
    assert actual == tc.expected
