from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class QueryParamCase:
    expected: httpx.QueryParams
