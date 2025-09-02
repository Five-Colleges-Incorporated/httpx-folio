from __future__ import annotations

from dataclasses import dataclass, field

from pytest_cases import parametrize_with_cases

from httpx_folio.query import DEFAULT_PAGE_SIZE


@dataclass(frozen=True)
class IntegrationOkTestCase:
    endpoint: str
    query: str | None = None


class IntegrationOkTestCases:
    def case_nonerm_noquery(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase("/coursereserves/courses")

    def case_erm_noquery(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase("/erm/org")

    def case_nonerm_query(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase(
            "/coursereserves/courses",
            'department.name = "German Studies"',
        )

    def case_erm_query(self) -> IntegrationOkTestCase:
        return IntegrationOkTestCase("/erm/org", "name=~A")


class TestIntegration:
    @parametrize_with_cases("tc", cases=IntegrationOkTestCases)
    def test_ok(self, tc: IntegrationOkTestCase) -> None:
        from httpx_folio.factories import FolioParams
        from httpx_folio.factories import (
            default_client_factory as make_client_factory,
        )
        from httpx_folio.query import QueryParams as uut

        with make_client_factory(
            FolioParams(
                "https://folio-etesting-snapshot-kong.ci.folio.org",
                "diku",
                "diku_admin",
                "admin",
            ),
        )() as client:
            res = client.get(tc.endpoint, params=uut(tc.query).normalized())
            res.raise_for_status()

            j = res.json()
            assert j["totalRecords"] > 1
            assert len(j[next(iter(j.keys()))])


@dataclass(frozen=True)
class NormalizedCase:
    query: str | None = None
    expected_query: str | None = None
    expected_filters: str | None = None

    limit: int | None = None
    expected_limit: str | None = None
    expected_perPage: str | None = None  # noqa: N815

    expected_keys: set[str] = field(default_factory=set)


class NormalizedCases:
    def case_default(self) -> NormalizedCase:
        return NormalizedCase(
            expected_query="cql.allRecords=1",
            expected_limit=str(DEFAULT_PAGE_SIZE),
            expected_perPage=str(DEFAULT_PAGE_SIZE),
            expected_keys={"stats"},
        )

    def case_largepage(self) -> NormalizedCase:
        return NormalizedCase(
            limit=10000,
            expected_query="cql.allRecords=1",
            expected_limit="10000",
            expected_perPage="10000",
            expected_keys={"stats"},
        )

    def case_simple_query(self) -> NormalizedCase:
        return NormalizedCase(
            query="simple query",
            expected_query="simple query",
            expected_filters="simple query",
            expected_limit=str(DEFAULT_PAGE_SIZE),
            expected_perPage=str(DEFAULT_PAGE_SIZE),
            expected_keys={"stats"},
        )


@parametrize_with_cases("tc", cases=NormalizedCases)
def test_normalized(tc: NormalizedCase) -> None:
    from httpx_folio.query import QueryParams as uut

    actual = (
        uut(tc.query) if tc.limit is None else uut(tc.query, tc.limit)
    ).normalized()

    if tc.expected_query is not None:
        tc.expected_keys.add("query")
        assert actual["query"] == tc.expected_query
    if tc.expected_filters is not None:
        tc.expected_keys.add("filters")
        assert actual["filters"] == tc.expected_filters
    if tc.expected_limit is not None:
        tc.expected_keys.add("limit")
        assert actual["limit"] == tc.expected_limit
    if tc.expected_perPage is not None:
        tc.expected_keys.add("perPage")
        assert actual["perPage"] == tc.expected_perPage

    assert set(actual.keys()) - set(tc.expected_keys) == set()
