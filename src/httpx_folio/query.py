"""A compatibility layer over FOLIO query parameters."""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Union, cast

import httpx

DEFAULT_PAGE_SIZE = 100

QueryType = Union[
    str,
    httpx.QueryParams,
    dict[
        str,
        Union[
            Union[str, int, float, bool],
            Sequence[Union[str, int, float, bool]],
        ],
    ],
]


class QueryParams:
    """An container for generating query parameters."""

    _cql_re = re.compile(r"^.*sortby.*$", re.IGNORECASE)

    def __init__(
        self,
        query: QueryType | None,
        limit: int = DEFAULT_PAGE_SIZE,
    ):
        """Initializes a base set of query parameters to generate variations."""
        self._limit = limit

        self._query: list[str] = []
        self._is_erm: bool | None = None
        self._is_cql: bool | None = None

        if query is None:
            return

        if isinstance(query, str):
            self._query = [query]
            if self._cql_re.match(query):
                self._is_erm = False
                self._is_cql = True

        if isinstance(query, (dict, httpx.QueryParams)):
            # Queries and filters could be hiding

            if q := query.get("query"):
                if not isinstance(q, str):
                    msg = f"Unexpected value {q} for query parameter."
                    raise ValueError(msg)
                self._query = [q]
                self._is_erm = False
                self._is_cql = True

            if "filters" in query:
                self._is_erm = True
                self._is_cql = False

                if isinstance(query, httpx.QueryParams):
                    self._query = query.get_list("filters")
                else:
                    q = query["filters"]
                    if isinstance(q, str):
                        self._query = [q]
                    elif isinstance(q, Sequence):
                        self._query = list(cast("Sequence[str]", query["filters"]))

                if not all(isinstance(v, str) for v in self._query):
                    msg = f"Unexpected value {q} for filter parameter."
                    raise ValueError(msg)

    def normalized(self) -> httpx.QueryParams:
        """Parameters compatible with all FOLIO endpoints.

        Different endpoints have different practices for sorting and filtering.
        The biggest change is between ERM and non-ERM. This will duplicate the
        parameters to work across both (and more as they're discovered).

        This also normalizes the return values of the ERM endpoints which by default
        to not return stats making them a different shape than other endpoints.
        """
        params = httpx.QueryParams()
        # add cql params if it is or might be cql
        if self._is_cql is None or self._is_cql:
            params = params.merge(
                {
                    # Most endpoints use query,
                    # only some are ok without cql.allRecords but they're all ok with it
                    "query": self._query[0]
                    if len(self._query) == 1
                    else "cql.allRecords=1",
                    "limit": self._limit,
                },
            )

        # add erm params if it is or might be erm
        if self._is_erm is None or self._is_erm:
            # ERM uses the filters property, it is fine without a cql.allRecords
            for q in self._query:
                params = params.add("filters", q)
            params = params.merge(
                {
                    "perPage": self._limit,
                    # ERM doesn't return the allRecords count unless stats is passed
                    "stats": True,
                },
            )
        return params
