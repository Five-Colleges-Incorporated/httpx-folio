from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import httpx
from pytest_cases import parametrize, parametrize_with_cases

from httpx_folio.query import DEFAULT_PAGE_SIZE, QueryType

from . import QueryParamCase


@dataclass(frozen=True)
class IdPagingCase(QueryParamCase):
    expected_fifteenth_page: httpx.QueryParams
    query: QueryType | None = None
    limit: int | None = None

    lowest_id: ClassVar[str] = "00000000-0000-0000-0000-000000000000"
    last_id: ClassVar[str] = "a88e5d82-96f7-4d9f-b7d6-1504c3b26a3d"
    highest_id: ClassVar[str] = "99999999-9999-9999-9999-999999999999"


class IdPagingCases:
    def case_default(self) -> IdPagingCase:
        return IdPagingCase(
            expected=httpx.QueryParams(
                f"query=id>{IdPagingCase.lowest_id} sortBy id"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=id;asc"
                f"&filters=id>{IdPagingCase.lowest_id}",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                f"query=id>{IdPagingCase.last_id} sortBy id"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=id;asc"
                f"&filters=id>{IdPagingCase.last_id}",
            ),
        )

    def case_simple_query(self) -> IdPagingCase:
        return IdPagingCase(
            query="simple query",
            expected=httpx.QueryParams(
                f"query=id>{IdPagingCase.lowest_id} and (simple query) sortBy id"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=id;asc"
                f"&filters=simple query&filters=id>{IdPagingCase.lowest_id}",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                f"query=id>{IdPagingCase.last_id} and (simple query) sortBy id"
                f"&limit={DEFAULT_PAGE_SIZE}&perPage={DEFAULT_PAGE_SIZE}"
                "&stats=true&sort=id;asc"
                f"&filters=simple query&filters=id>{IdPagingCase.last_id}",
            ),
        )

    @parametrize(
        query=[
            {"query": "cql.allRecords=1"},
            "cql.allRecords=1 sortBy id asc",
            "cql.allRecords=1 sortBy id ASC",
            "cql.allRecords=1 sortby id asc",
            "cql.allRecords=1 sortby id ASC",
            "cql.allRecords=1 SORTBY id asc",
            "cql.allRecords=1 SORTBY id ASC",
            "cql.allRecords=1 sortBy id/sort.ascending",
            "cql.allRecords=1 sortBy id/sort.asc",
            "cql.allRecords=1 sortby id/sort.ascending",
            "cql.allRecords=1 sortby id/sort.asc",
            "cql.allRecords=1 SORTBY id/sort.ascending",
            "cql.allRecords=1 SORTBY id/sort.ascending",
        ],
    )
    def case_ascending_default_cql(self, query: QueryType) -> IdPagingCase:
        return IdPagingCase(
            query=query,
            expected=httpx.QueryParams(
                f"query=id>{IdPagingCase.lowest_id} sortBy id"
                f"&limit={DEFAULT_PAGE_SIZE}",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                f"query=id>{IdPagingCase.last_id} sortBy id&limit={DEFAULT_PAGE_SIZE}",
            ),
        )

    @parametrize(
        query=[
            "cql.allRecords=1 sortBy id desc",
            "cql.allRecords=1 sortBy id DESC",
            "cql.allRecords=1 sortby id desc",
            "cql.allRecords=1 sortby id DESC",
            "cql.allRecords=1 SORTBY id desc",
            "cql.allRecords=1 SORTBY id DESC",
            "cql.allRecords=1 sortBy id/sort.descending",
            "cql.allRecords=1 sortBy id/sort.desc",
            "cql.allRecords=1 sortby id/sort.descending",
            "cql.allRecords=1 sortby id/sort.desc",
            "cql.allRecords=1 SORTBY id/sort.descending",
            "cql.allRecords=1 SORTBY id/sort.descending",
        ],
    )
    def case_descending_default_cql(self, query: str) -> IdPagingCase:
        return IdPagingCase(
            query=query,
            expected=httpx.QueryParams(
                f"query=id<{IdPagingCase.highest_id} sortBy id/sort.descending"
                f"&limit={DEFAULT_PAGE_SIZE}",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                f"query=id<{IdPagingCase.last_id} sortBy id/sort.descending"
                f"&limit={DEFAULT_PAGE_SIZE}",
            ),
        )


@parametrize_with_cases("tc", cases=IdPagingCases)
def test_id_paging(tc: IdPagingCase) -> None:
    from httpx_folio.query import QueryParams as uut

    first_page = (
        uut(tc.query) if tc.limit is None else uut(tc.query, tc.limit)
    ).id_paging()

    assert first_page == tc.expected

    nth_page = (
        uut(tc.query) if tc.limit is None else uut(tc.query, tc.limit)
    ).id_paging(tc.last_id)
    assert nth_page == tc.expected_fifteenth_page
