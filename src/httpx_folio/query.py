"""A compatibility layer over FOLIO query parameters with common paging scenarios."""

from __future__ import annotations

import re
from collections.abc import Sequence
from enum import IntEnum
from typing import Annotated, Union, cast

import httpx

DEFAULT_PAGE_SIZE = 100
ERM_MAX_PERPAGE = 100
CQL_ALL_RECORDS = "cql.allRecords=1"

QueryType = Annotated[
    Union[
        str,
        httpx.QueryParams,
        dict[
            str,
            Union[
                Union[str, int, float, bool],
                Sequence[Union[str, int, float, bool]],
            ],
        ],
    ],
    "A simplified version of HTTPX's QueryParamTypes.",
]


class QueryParams:
    """An container for generating HTTPX QueryParams with FOLIO quirks."""

    def __init__(
        self,
        query: QueryType | None,
        limit: int = DEFAULT_PAGE_SIZE,
    ):
        """Initializes a base set of query parameters to generate variations.

        Raises:
            TypeError: If the query or filter key is not parseable as a string.
        """
        self._limit = limit

        self._query: list[str] = []
        self._base_query: str | None = None
        self._is_erm: bool | None = None
        self._is_cql: bool | None = None
        self._sort_type = _SortType.UNSORTED

        if query is None:
            self._additional_params = httpx.QueryParams()
            return

        parser = _QueryParser(query)
        self._additional_params = parser.additional_params()

        (q, qc, is_cql) = parser.check_string()
        if q is not None:
            self._query = [q]
        if qc is not None:
            self._base_query = qc
        if is_cql:
            self._is_erm = False
            self._is_cql = True

        # Queries and filters could be hiding
        (q, qc, is_cql) = parser.check_query()
        if q is not None:
            self._query = [q]
        if qc is not None:
            self._base_query = qc
        if is_cql:
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

        self._sort_type = parser.check_sort()

    def normalized(self) -> httpx.QueryParams:
        """Parameters compatible with all FOLIO endpoints.

        Different endpoints have different practices for sorting and filtering.
        The biggest change is between ERM and non-ERM. This will duplicate the
        parameters to work across both (and more as they're discovered).

        This also normalizes the return values of ERM endpoints which by default
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
                    else CQL_ALL_RECORDS,
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
        """Parameters for a single record to get the shape and totalRecord count.

        Zero or One records will be returned regardless of the current limit.
        """
        params = self.normalized()
        # add a sort so null records go to the end
        if "query" in params and self._sort_type == _SortType.UNSORTED:
            params = params.set("query", params["query"] + " sortBy id")
        if ("sort" not in params) and (self._is_erm is None or self._is_erm):
            params = params.add("sort", "id;asc")

        # override the limit
        if "limit" in params:
            params = params.set("limit", 1)
        if "perPage" in params:
            params = params.set("perPage", 1)

        return params

    def offset_paging(self, page: int = 1) -> httpx.QueryParams:
        """Parameters for a single one-based page of results.

        Paging by offset has performance issues for large offsets.
        If possible use id_paging instead.

        If the endpoint to be paged has no id field, a sort on another field
        must be specified. Use stats() to determine whether the records
        contain an id field. Calling offset_paging() in this scenario will appear
        to succeed but may have missing or duplicated results.

        ERM has a hard maximum limit of 100 results which impacts this paging.
        If the current parameter set is known to be ERM then each page
        will have at most 100 records even if the limit was set higher.
        If the current parameter set is ambigous ERM paging parameters will be
        omitted if the limit is set over 100 to avoid missing data.
        """
        params = self.normalized()
        # add a sort so results are pageable
        if "query" in params and self._sort_type == _SortType.UNSORTED:
            params = params.set("query", params["query"] + " sortBy id")

        if ("sort" not in params) and (self._is_erm is None or self._is_erm):
            params = params.add("sort", "id;asc")

        if self._is_erm is None and self._limit > ERM_MAX_PERPAGE:
            # page size can't be normalized if it is over 100
            params = params.remove("stats")
            params = params.remove("sort")
            params = params.remove("perPage")

        limit = self._limit
        if self._is_erm:
            # ERM has a max page size of 100
            # if we know we're paging ERM then we'll override the provided page size
            limit = min(limit, ERM_MAX_PERPAGE)
            params = params.set("perPage", limit)

        return params.set("offset", (page - 1) * limit)

    def can_page_by_id(self) -> bool:
        """Indicates whether the current set of parameters supports id_paging."""
        return self._sort_type != _SortType.NONSTANDARD

    def id_paging(self, last_id: str | None = None) -> httpx.QueryParams:
        """Parameters for a single page of results.

        Paging by id is not supported for queries sorted on non-id fields. Use
        offset_paging instead, can_page_by_id() will tell you if id paging is supported.

        Paging by id is not supported for endpoints that do not have an id field. Use
        stats() to determine whether the records contain an id field. Calling
        id_paging() in this scenario will appear to succeed
        but may have missing or duplicated results.

        Raises:
            RuntimeError: If can_page_by_id() is False
        """
        if not self.can_page_by_id():
            msg = (
                "Id Paging is not supported in the current parameter configuration."
                "Use Offset Paging instead."
            )
            raise RuntimeError(msg)

        params = self.normalized()

        last_id = last_id or (
            "99999999-9999-9999-9999-999999999999"
            if self._sort_type == _SortType.DESCENDING
            else "00000000-0000-0000-0000-000000000000"
        )

        if self._is_cql is None or self._is_cql:
            q = (
                f"id<{last_id}"
                if self._sort_type == _SortType.DESCENDING
                else f"id>{last_id}"
            )
            if self._base_query is not None:
                q += f" and ({self._base_query})"
            elif len(self._query) == 1:
                q += f" and ({self._query[0]})"

            params = params.set(
                "query",
                f"{q} sortBy id/sort.descending"
                if self._sort_type == _SortType.DESCENDING
                else f"{q} sortBy id",
            )

        if self._is_erm is None or self._is_erm:
            params = params.set(
                "sort",
                "id;desc" if self._sort_type == _SortType.DESCENDING else "id;asc",
            )
            params = params.add(
                "filters",
                f"id<{last_id}"
                if self._sort_type == _SortType.DESCENDING
                else f"id>{last_id}",
            )

        return params


class _SortType(IntEnum):
    UNSORTED = 0
    NONSTANDARD = 1
    ASCENDING = 2
    DESCENDING = 4


class _QueryParser:
    _cql_re = re.compile(
        r"^(?:(?:(.*?)(?:sortby.*))|(cql\..*)(?:sortby.*)?)$",
        re.IGNORECASE,
    )
    _sort_re = re.compile(
        r"^.*sortby(?:\s+(id)(?:(?:(?:\/sort\.)|\s+)?((?:asc)|(?:desc))(?:ending)?)?)?.*$",
        re.IGNORECASE,
    )

    def __init__(self, query: QueryType):
        self.query = query

    @staticmethod
    def _check_str_base_query(q: str) -> tuple[str | None, bool]:
        if not (m := _QueryParser._cql_re.match(q)):
            return (None, False)

        if (q := m.group(1)) and isinstance(q, str):
            return (q.strip(), True)

        if (q := m.group(2)) and isinstance(q, str):
            return (q.strip(), True)

        return (None, True)

    def check_string(self) -> tuple[str | None, str | None, bool | None]:
        if self.query is None or not isinstance(self.query, str):
            return (None, None, None)

        return (self.query, *self._check_str_base_query(self.query))

    def check_query(self) -> tuple[str | None, str | None, bool | None]:
        if not isinstance(self.query, (dict, httpx.QueryParams)):
            return (None, None, None)

        if "query" not in self.query:
            return (None, None, False)

        if isinstance(self.query, dict):
            q = self.query["query"]
            if not isinstance(q, str):
                msg = f"Unexpected value {q} for query parameter."
                raise TypeError(msg)
            (qb, _) = self._check_str_base_query(q)
            return (q, qb, True)

        qs = self.query.get_list("query")
        if len(qs) == 1 and isinstance(qs[0], str):
            (qc, _) = self._check_str_base_query(qs[0])
            return (qs[0], qc, True)

        msg = f"Unexpected value {self.query['query']} for query parameter."
        raise TypeError(msg)

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
        raise TypeError(msg)

    def check_erm(self) -> bool:
        return isinstance(self.query, (dict, httpx.QueryParams)) and (
            "sort" in self.query or "filters" in self.query
        )

    @staticmethod
    def _check_str_sort(q: str) -> _SortType:
        if not (m := _QueryParser._sort_re.match(q)):
            return _SortType.UNSORTED

        if not m.group(1):
            return _SortType.NONSTANDARD

        if not (s := m.group(2)):
            return _SortType.ASCENDING

        if not isinstance(s, str):
            msg = f"Unexpected value {s} for query parameter."
            raise TypeError(msg)

        if s.lower().strip() == "asc":
            return _SortType.ASCENDING
        if s.lower().strip() == "desc":
            return _SortType.DESCENDING

        return _SortType.NONSTANDARD

    def check_sort(self) -> _SortType:
        if isinstance(self.query, str):
            return _QueryParser._check_str_sort(self.query)

        if isinstance(self.query, (dict, httpx.QueryParams)):
            if q := self.query.get("query", None):
                if not isinstance(q, str):
                    msg = f"Unexpected value {q} for query parameter."
                    raise TypeError(msg)
                return _QueryParser._check_str_sort(q)

            if s := self.query.get("sort", None):
                if not isinstance(s, str):
                    msg = f"Unexpected value {s} for sort parameter."
                    raise TypeError(msg)
                if s.lower().strip() == "id;asc":
                    return _SortType.ASCENDING
                if s.lower().strip() == "id;desc":
                    return _SortType.DESCENDING
                return _SortType.NONSTANDARD

        return _SortType.UNSORTED

    _reserved = frozenset({"query", "filters", "limit", "perPage", "offset", "stats"})

    def additional_params(self) -> httpx.QueryParams:
        if not isinstance(self.query, (dict, httpx.QueryParams)):
            return httpx.QueryParams()

        query = httpx.QueryParams(self.query)
        if isinstance(query, httpx.QueryParams):
            for r in self._reserved:
                query = query.remove(r)
        return query
