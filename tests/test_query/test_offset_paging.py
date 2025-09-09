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
    key: str | None = None


class OffsetPagingCases:
    def case_indeterminate_default(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            expected=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=id;asc&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                f"&stats=true&sort=id;asc&offset={DEFAULT_PAGE_SIZE * 14}",
            ),
        )

    def case_indeterminate_simple_query(self) -> OffsetPagingCase:
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
                f"&stats=true&sort=id;asc&offset={DEFAULT_PAGE_SIZE * 14}",
            ),
        )

    def case_indeterminate_bigger_page(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            limit=1000,
            expected=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id&limit=1000&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id&limit=1000&offset=14000",
            ),
        )

    def case_indeterminate_smaller_page(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            limit=50,
            expected=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id&limit=50"
                "&perPage=50&stats=true&sort=id;asc"
                "&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "query=cql.allRecords=1 sortBy id&limit=50"
                "&perPage=50&stats=true&sort=id;asc"
                "&offset=700",
            ),
        )

    @parametrize(
        query=[
            {"query": "some query"},
            "cql.allRecords=1",
            "cql.allIndices=fish",
        ],
    )
    def case_cql_unsorted(self, query: QueryType) -> OffsetPagingCase:
        expected = query["query"] if isinstance(query, dict) else query
        return OffsetPagingCase(
            query=query,
            expected=httpx.QueryParams(
                f"query={expected} sortBy id&limit={DEFAULT_PAGE_SIZE}&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                f"query={expected} sortBy id"
                f"&limit={DEFAULT_PAGE_SIZE}&offset={DEFAULT_PAGE_SIZE * 14}",
            ),
        )

    @parametrize(
        query=[
            {"query": "some query"},
            "cql.allRecords=1",
            "cql.allIndices=fish",
        ],
    )
    def case_cql_unsorted_no_id(self, query: QueryType) -> OffsetPagingCase:
        expected = query["query"] if isinstance(query, dict) else query
        return OffsetPagingCase(
            query=query,
            key="index",
            expected=httpx.QueryParams(
                f"query={expected} sortBy index&limit={DEFAULT_PAGE_SIZE}&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                f"query={expected} sortBy index"
                f"&limit={DEFAULT_PAGE_SIZE}&offset={DEFAULT_PAGE_SIZE * 14}",
            ),
        )

    @parametrize(
        query=[
            {"query": "some query sortBy index"},
            {"query": "some query SORTBY index"},
            {"query": "some query sortby index"},
            {"query": "some query sortby index asc"},
            {"query": "some query sortby index desc"},
            {"query": "some query sortby index/sort.asc"},
            {"query": "some query sortby index/sort.desc"},
            "cql.allRecords=1 sortBy index",
            "cql.allIndices=fish SORTBY index",
            "cql.allRecords=1 sortby index",
            "cql.allIndices=fish sortby index asc",
            "cql.allRecords=1 sortby index desc",
            "cql.allIndices=fish sortby index/sort.asc",
            "cql.allRecords=1 sortby index/sort.desc",
        ],
    )
    def case_cql_sorted(self, query: QueryType) -> OffsetPagingCase:
        expected = query["query"] if isinstance(query, dict) else query
        return OffsetPagingCase(
            query=query,
            key="xedni",  # ignored because a sort is specified
            expected=httpx.QueryParams(
                f"query={expected}&limit={DEFAULT_PAGE_SIZE}&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                f"query={expected}"
                f"&limit={DEFAULT_PAGE_SIZE}&offset={DEFAULT_PAGE_SIZE * 14}",
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
                f"&offset={DEFAULT_PAGE_SIZE * 14}",
            ),
        )

    def case_erm_unsorted_no_id(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            query={"filters": "simple query"},
            key="index",
            expected=httpx.QueryParams(
                "filters=simple query"
                f"&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=index;asc&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "filters=simple query"
                f"&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=index;asc"
                f"&offset={DEFAULT_PAGE_SIZE * 14}",
            ),
        )

    def case_erm_sorted(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            query={"filters": "simple query", "sort": "index;desc"},
            key="xedni",  # ignored because a sort is specified
            expected=httpx.QueryParams(
                "filters=simple query"
                f"&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=index;desc&offset=0",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                "filters=simple query"
                f"&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=index;desc"
                f"&offset={DEFAULT_PAGE_SIZE * 14}",
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
                f"&offset={ERM_MAX_PERPAGE * 14}",
            ),
        )


@parametrize_with_cases("tc", cases=OffsetPagingCases)
def test_offset_paging(tc: OffsetPagingCase) -> None:
    from httpx_folio.query import QueryParams

    uut = QueryParams(tc.query) if tc.limit is None else QueryParams(tc.query, tc.limit)
    first_page = (
        uut.offset_paging() if tc.key is None else uut.offset_paging(key=tc.key)
    )

    assert first_page == tc.expected

    nth_page = (
        uut.offset_paging(page=15)
        if tc.key is None
        else uut.offset_paging(key=tc.key, page=15)
    )
    assert nth_page == tc.expected_fifteenth_page
