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


class _QueryParser:
    _cql_re = re.compile(r"^.*sortby.*$", re.IGNORECASE)
    _sort_re = re.compile(r"^.*sortby.*$", re.IGNORECASE)

    def __init__(self, query: QueryType):
        self.query = query

    def check_string(self) -> tuple[str | None, bool]:
        return (
            (None, False)
            if not isinstance(self.query, str)
            else (self.query, self._cql_re.match(self.query) is not None)
        )

    def check_query(self) -> str | None:
        if (
            not isinstance(self.query, (dict, httpx.QueryParams))
            or "query" not in self.query
        ):
            return None

        if isinstance(self.query, dict):
            if q := self.query["query"]:
                if not isinstance(q, str):
                    msg = f"Unexpected value {q} for query parameter."
                    raise ValueError(msg)
                return q
            return None

        if qs := self.query.get_list("query"):
            if len(qs) == 0:
                return None
            if len(qs) == 1 and isinstance(qs[0], str):
                return qs[0]

        msg = f"Unexpected value {self.query['query']} for query parameter."
        raise ValueError(msg)

    def check_filters(self) -> list[str] | None:
        if (
            not isinstance(self.query, (dict, httpx.QueryParams))
            or "filters" not in self.query
        ):
            return None

        filters = []
        if isinstance(self.query, httpx.QueryParams):
            filters = self.query.get_list("filters")
        else:
            q = self.query["filters"]
            if isinstance(q, str):
                filters = [q]
            elif isinstance(q, Sequence):
                filters = list(cast("Sequence[str]", self.query["filters"]))

        if all(isinstance(v, str) for v in filters):
            return filters

        msg = f"Unexpected value {self.query['filters']} for filter parameter."
        raise ValueError(msg)

    def check_erm(self) -> bool:
        return (
            isinstance(self.query, (dict, httpx.QueryParams)) and "sort" in self.query
        )

    def check_sort(self) -> bool:
        if isinstance(self.query, str):
            return self._sort_re.match(self.query) is not None

        if isinstance(self.query, (dict, httpx.QueryParams)):
            if q := self.query.get("query", None):
                return isinstance(q, str) and self._sort_re.match(q) is not None

            if "sort" in self.query:
                return True

        return False

    _reserved = frozenset({"query", "filters", "limit", "perPage", "offset", "stats"})

    def additional_params(self) -> httpx.QueryParams:
        if not isinstance(self.query, (dict, httpx.QueryParams)):
            return httpx.QueryParams()

        query = httpx.QueryParams(self.query)
        if isinstance(query, httpx.QueryParams):
            for r in self._reserved:
                query = query.remove(r)
        return query


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
        self._is_sorted = False

        if query is None:
            self._additional_params = httpx.QueryParams()
            return

        parser = _QueryParser(query)
        self._additional_params = parser.additional_params()

        (q, is_cql) = parser.check_string()
        if q is not None:
            self._query = [q]
        if is_cql:
            self._is_erm = False
            self._is_cql = True

        # Queries and filters could be hiding
        cql_query = parser.check_query()
        if cql_query is not None:
            self._query = [cql_query]
            self._is_erm = False
            self._is_cql = True

        filters = parser.check_filters()
        if filters is not None:
            self._query = filters
            self._is_erm = True
            self._is_cql = False

        if parser.check_erm():
            self._is_erm = True
            self._is_cql = False

        if parser.check_sort():
            self._is_sorted = True

    def normalized(self) -> httpx.QueryParams:
        """Parameters compatible with all FOLIO endpoints.

        Different endpoints have different practices for sorting and filtering.
        The biggest change is between ERM and non-ERM. This will duplicate the
        parameters to work across both (and more as they're discovered).

        This also normalizes the return values of the ERM endpoints which by default
        to not return stats making them a different shape than other endpoints.
        """
        params = self._additional_params
        # add cql params if it is or might be cql
        if self._is_cql is None or self._is_cql:
            params = params.merge(
                {
                    # CQL endpoints use query,
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

    def stats(self) -> httpx.QueryParams:
        """Parameters for a single row to get the shape and totalRecord count.

        Zero or One records will be returned regardless of the endpoint's
        sorting/filtering practices.
        """
        params = self.normalized()
        # add a sort so null records go to the end
        if "query" in params and not self._is_sorted:
            params = params.set("query", params["query"] + " sortBy id")
        if ("sort" not in params) and (self._is_erm is None or self._is_erm):
            params = params.add("sort", "id;asc")

        # override the limit
        if "limit" in params:
            params = params.set("limit", 1)
        if "perPage" in params:
            params = params.set("perPage", 1)

        return params

    def offset_paging(self, page: int | None = None) -> httpx.QueryParams:
        """Parameters for a single page of results."""
        params = self.normalized()
        # add a sort so null records go to the end
        if "query" in params and not self._is_sorted:
            params = params.set("query", params["query"] + " sortBy id")
        if ("sort" not in params) and (self._is_erm is None or self._is_erm):
            params = params.add("sort", "id;asc")

        return params.set("offset", (page or 0) * self._limit)
