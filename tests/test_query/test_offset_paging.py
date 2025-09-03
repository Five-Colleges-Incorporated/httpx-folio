from __future__ import annotations

from dataclasses import dataclass

import httpx
from pytest_cases import parametrize, parametrize_with_cases

from httpx_folio.query import DEFAULT_PAGE_SIZE, ERM_MAX_PERPAGE, QueryType

from . import QueryParamCase


@dataclass(frozen=True)
class OffsetPagingCase(QueryParamCase):
    expected_fifteenth_page: httpx.QueryParams
    query: QueryType | None = None
    limit: int | None = None


class OffsetPagingCases:
    def case_default(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            expected=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=id;asc&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                f"&stats=true&sort=id;asc&offset={DEFAULT_PAGE_SIZE * 15}",
            ),
        )

    def case_simple_query(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            query="simple query",
            expected=httpx.QueryParams(
                "query=simple query sortBy id&filters=simple query"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=id;asc&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "query=simple query sortBy id&filters=simple query"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                f"&stats=true&sort=id;asc&offset={DEFAULT_PAGE_SIZE * 15}",
            ),
        )

    def case_bigger_page_default(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            limit=1000,
            expected=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id&limit=1000&stats=true&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id&limit=1000&stats=true&offset=15000",
            ),
        )

    def case_smaller_page_default(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            limit=50,
            expected=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id"
                "&limit=50&perPage=50"
                "&stats=true&sort=id;asc&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id"
                "&limit=50&perPage=50"
                "&stats=true&sort=id;asc&offset=750",
            ),
        )

    def case_cql_unsorted(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            query={"query": "simple query"},
            expected=httpx.QueryParams(
                f"query=simple query sortBy id&limit={DEFAULT_PAGE_SIZE}&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "query=simple query sortBy id"
                f"&limit={DEFAULT_PAGE_SIZE}&offset={DEFAULT_PAGE_SIZE * 15}",
            ),
        )

    @parametrize(
        query=[
            "simple query sortby index",
            "simple query sortBy index",
            "simple query SORTBY index",
        ],
    )
    def case_cql_sorted(self, query: str) -> OffsetPagingCase:
        return OffsetPagingCase(
            query=query,
            expected=httpx.QueryParams(
                f"query={query}&limit={DEFAULT_PAGE_SIZE}&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                f"query={query}"
                f"&limit={DEFAULT_PAGE_SIZE}&offset={DEFAULT_PAGE_SIZE * 15}",
            ),
        )

    def case_erm_unsorted(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            query={"filters": "simple query"},
            expected=httpx.QueryParams(
                "filters=simple query"
                f"&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=id;asc&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "filters=simple query"
                f"&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=id;asc"
                f"&offset={DEFAULT_PAGE_SIZE * 15}",
            ),
        )

    def case_erm_sorted(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            query={"filters": "simple query", "sort": "index;desc"},
            expected=httpx.QueryParams(
                "filters=simple query"
                f"&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=index;desc&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "filters=simple query"
                f"&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=index;desc"
                f"&offset={DEFAULT_PAGE_SIZE * 15}",
            ),
        )

    def case_erm_hardlimit(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            query={"filters": "simple query"},
            limit=1000,
            expected=httpx.QueryParams(
                "filters=simple query"
                f"&perPage={ERM_MAX_PERPAGE}"
                "&stats=true&sort=id;asc&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "filters=simple query"
                f"&perPage={ERM_MAX_PERPAGE}"
                "&stats=true&sort=id;asc"
                f"&offset={ERM_MAX_PERPAGE * 15}",
            ),
        )


@parametrize_with_cases("tc", cases=OffsetPagingCases)
def test_stats(tc: OffsetPagingCase) -> None:
    from httpx_folio.query import QueryParams as uut

    first_page = (
        uut(tc.query) if tc.limit is None else uut(tc.query, tc.limit)
    ).offset_paging()

    assert first_page == tc.expected

    nth_page = (
        uut(tc.query) if tc.limit is None else uut(tc.query, tc.limit)
    ).offset_paging(page=15)
    assert nth_page == tc.expected_fifteenth_page
