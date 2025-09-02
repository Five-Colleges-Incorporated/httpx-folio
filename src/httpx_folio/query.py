"""A compatibility layer over FOLIO query parameters."""

from __future__ import annotations

import httpx

DEFAULT_PAGE_SIZE = 100


class QueryParams:
    """An container for generating query parameters."""

    def __init__(
        self,
        query: str | None = None,
        limit: int = DEFAULT_PAGE_SIZE,
    ):
        """Initializes a base set of query parameters to generate variations."""
        self._query = query
        self._limit = limit

    def normalized(self) -> httpx.QueryParams:
        """Parameters compatible with all FOLIO endpoints.

        Different endpoints have different practices for sorting and filtering.
        The biggest change is between ERM and non-ERM. This will duplicate the
        parameters to work across both (and more as they're discovered).

        This also normalizes the return values of the ERM endpoints which by default
        to not return stats making them a different shape than other endpoints.
        """
        params = httpx.QueryParams(
            {
                # Most endpoints use query,
                # only some are ok without cql.allRecords they're all ok with it
                "query": self._query if self._query is not None else "cql.allRecords=1",
                # limit and perPage seem to be the only parameters limiting results
                "limit": self._limit,
                "perPage": self._limit,
                # ERM doesn't return the allRecords count unless stats is passed
                "stats": True,
            },
        )
        if self._query is not None:
            # ERM uses the filters property, it is fine without a cql.allRecords
            params = params.add("filters", self._query)
        return params
