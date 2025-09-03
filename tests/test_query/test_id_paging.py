from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

import httpx
from pytest_cases import parametrize_with_cases

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


@parametrize_with_cases("tc", cases=IdPagingCases)
def test_stats(tc: IdPagingCase) -> None:
    from httpx_folio.query import QueryParams as uut

    first_page = (
        uut(tc.query) if tc.limit is None else uut(tc.query, tc.limit)
    ).id_paging()

    assert first_page == tc.expected

    nth_page = (
        uut(tc.query) if tc.limit is None else uut(tc.query, tc.limit)
    ).id_paging(tc.last_id)
    assert nth_page == tc.expected_fifteenth_page
