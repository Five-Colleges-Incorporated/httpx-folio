from __future__ import annotations

from dataclasses import dataclass

import httpx
from pytest_cases import parametrize_with_cases

from httpx_folio.query import DEFAULT_PAGE_SIZE, QueryType


@dataclass(frozen=True)
class OffsetPagingCase:
    expected_first_page: httpx.QueryParams
    expected_fifteenth_page: httpx.QueryParams
    query: QueryType | None = None
    limit: int | None = None


class OffsetPagingCases:
    def case_default(self) -> OffsetPagingCase:
        return OffsetPagingCase(
            expected_first_page=httpx.QueryParams(
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


@parametrize_with_cases("tc", cases=OffsetPagingCases)
def test_stats(tc: OffsetPagingCase) -> None:
    from httpx_folio.query import QueryParams as uut

    first_page = (
        uut(tc.query) if tc.limit is None else uut(tc.query, tc.limit)
    ).offset_paging()

    assert first_page == tc.expected_first_page

    nth_page = (
        uut(tc.query) if tc.limit is None else uut(tc.query, tc.limit)
    ).offset_paging(page=15)
    assert nth_page == tc.expected_fifteenth_page
