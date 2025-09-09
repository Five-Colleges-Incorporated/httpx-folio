from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

import httpx
import pytest
from pytest_cases import parametrize, parametrize_with_cases

from httpx_folio.query import DEFAULT_PAGE_SIZE, QueryType

from . import QueryParamCase

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True)
class IdPagingCase(QueryParamCase):
    expected_fifteenth_page: httpx.QueryParams
    query: QueryType | None = None
    limit: int | None = None

    lowest_id: ClassVar[str] = "00000000-0000-0000-0000-000000000000"
    last_id: ClassVar[str] = "a88e5d82-96f7-4d9f-b7d6-1504c3b26a3d"
    highest_id: ClassVar[str] = "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF"


def cql_sortbyid_generator() -> Iterator[tuple[str | dict[str, str], bool, str]]:
    sorts = ["sortby", "SORTBY", "sortBy"]
    asc = [
        "",
        " asc",
        " ascending",
        " ASC",
        "/sort.ascending",
        "/sort.asc",
        "/SORT.ASCENDING",
    ]
    desc = [
        " desc",
        " descending",
        " DESC",
        "/sort.descending",
        "/sort.desc",
        "/SORT.DESCENDING",
    ]
    queries = ["some query", "cql.allRecords=1", "cql.allIndexes=fish"]
    for s in sorts:
        for q in queries:
            for ad in [*asc, *desc]:
                query = f"{q} {s} id{ad}"
                yield (
                    query if q.startswith("cql") else {"query": query},
                    ad in asc,
                    q,
                )
                query = f"{q} {s} Id{ad}"
                yield (
                    query if q.startswith("cql") else {"query": query},
                    ad in asc,
                    q,
                )


def erm_sortbyid_generator() -> Iterator[tuple[dict[str, str | list[str]], bool, str]]:
    for ad in ["asc", "desc"]:
        yield (
            {"filters": "some filter", "sort": f"id;{ad}"},
            ad == "asc",
            "filters=some filter",
        )
        yield (
            {"filters": ["some", "filters"], "sort": f"id;{ad}"},
            ad == "asc",
            "filters=some&filters=filters",
        )


class IdPagingCases:
    def case_indeterminate_default(self) -> IdPagingCase:
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

    def case_indeterminate_simple_query(self) -> IdPagingCase:
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

    @parametrize(tc=list(cql_sortbyid_generator()))
    def case_cql_sortbyid(self, tc: tuple[QueryType, bool, str]) -> IdPagingCase:
        (query, is_asc, expected) = tc
        if is_asc:
            return IdPagingCase(
                query=query,
                expected=httpx.QueryParams(
                    f"query=id>{IdPagingCase.lowest_id} and ({expected}) sortBy id"
                    f"&limit={DEFAULT_PAGE_SIZE}",
                ),
                expected_fifteenth_page=httpx.QueryParams(
                    f"query=id>{IdPagingCase.last_id} and ({expected}) sortBy id"
                    f"&limit={DEFAULT_PAGE_SIZE}",
                ),
            )

        return IdPagingCase(
            query=query,
            expected=httpx.QueryParams(
                f"query=id<{IdPagingCase.highest_id} and ({expected}) "
                "sortBy id/sort.descending"
                f"&limit={DEFAULT_PAGE_SIZE}",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                f"query=id<{IdPagingCase.last_id} and ({expected}) "
                "sortBy id/sort.descending"
                f"&limit={DEFAULT_PAGE_SIZE}",
            ),
        )

    @parametrize(tc=list(erm_sortbyid_generator()))
    def case_erm_sortbyid(self, tc: tuple[QueryType, bool, str]) -> IdPagingCase:
        (query, is_asc, expected) = tc
        if is_asc:
            return IdPagingCase(
                query=query,
                expected=httpx.QueryParams(
                    f"sort=id;asc&{expected}&filters=id>{IdPagingCase.lowest_id}"
                    f"&perPage={DEFAULT_PAGE_SIZE}&stats=true",
                ),
                expected_fifteenth_page=httpx.QueryParams(
                    f"sort=id;asc&{expected}&filters=id>{IdPagingCase.last_id}"
                    f"&perPage={DEFAULT_PAGE_SIZE}&stats=true",
                ),
            )

        return IdPagingCase(
            query=query,
            expected=httpx.QueryParams(
                f"sort=id;desc&{expected}&filters=id<{IdPagingCase.highest_id}"
                f"&perPage={DEFAULT_PAGE_SIZE}&stats=true",
            ),
            expected_fifteenth_page=httpx.QueryParams(
                f"sort=id;desc&{expected}&filters=id<{IdPagingCase.last_id}"
                f"&perPage={DEFAULT_PAGE_SIZE}&stats=true",
            ),
        )


@parametrize_with_cases("tc", cases=IdPagingCases)
def test_id_paging(tc: IdPagingCase) -> None:
    from httpx_folio.query import QueryParams

    uut = QueryParams(tc.query) if tc.limit is None else QueryParams(tc.query, tc.limit)

    assert uut.can_page_by_id()

    first_page = uut.id_paging()
    assert first_page == tc.expected

    nth_page = uut.id_paging(last_id=tc.last_id)
    assert nth_page == tc.expected_fifteenth_page


@parametrize(
    query=[
        "some query sortBy index",
        "some query sortby index",
        "some query SORTBY index",
        "some query sortBy index asc",
        "some query sortby index asc",
        "some query SORTBY index asc",
        "some query sortBy index/sort.ascending",
        "some query sortby index/sort.ascending",
        "some query SORTBY index/sort.ascending",
        "some query sortBy index desc",
        "some query sortby index desc",
        "some query SORTBY index desc",
        "some query sortBy index/sort.descending",
        "some query sortby index/sort.descending",
        "some query SORTBY index/sort.descending",
        {"sort": "index;asc"},
        {"sort": "index;desc"},
    ],
)
def test_id_paging_not_supported(query: QueryType) -> None:
    from httpx_folio.query import QueryParams

    uut = QueryParams(query)

    assert not uut.can_page_by_id()

    with pytest.raises(RuntimeError):
        uut.id_paging()
