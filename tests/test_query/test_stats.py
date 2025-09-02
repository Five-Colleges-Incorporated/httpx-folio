from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import httpx
from pytest_cases import parametrize_with_cases

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


@parametrize_with_cases("tc", cases=StatsCases)
def test_normalized(tc: StatsCase) -> None:
    from httpx_folio.query import QueryParams as uut

    actual = uut(tc.query, 1000).stats()
    assert actual == tc.expected
