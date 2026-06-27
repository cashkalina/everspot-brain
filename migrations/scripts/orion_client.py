"""Thin authenticated Orion (Laravel Orion REST) client for Wave-0 read + reference create.

Orion exposes every resource with a uniform REST + ``POST /{resource}/search``
surface (filters, scopes, sorts, pagination). This client wraps just what the
migration pipeline needs: search, paginate-all, create, batch-store.

Auth (plan §2.1 — *this works today, it is not a bug*):
    - Tenant is selected **by domain** (``base_url`` points at e.g.
      ``https://acme.everspot.test/api``).
    - Send ``Authorization: Bearer <token>`` AND a ``user-id`` header naming the
      migration user (must hold the relevant Spatie ``{model}.viewAny/.create/.update``
      permissions). The middleware sets that user on the web guard; Sanctum's
      web-guard fallback hands it to Orion's policies. No code change needed.
    - The pipeline's egress IP must be **IP-whitelisted** on the sandbox tenant,
      and migration tokens are capped at 7 days (regenerate, or use a migration-token).

everspot-brain doc that specifies the rules:
    system-wiki/system/imports.md  ·  system-wiki/system/orion-api.md
"""

from __future__ import annotations

from typing import Any, Iterator, Optional, Sequence

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore

VERSION = "1.0.0"

DEFAULT_PAGE_SIZE = 100
DEFAULT_TIMEOUT = 30.0


class OrionError(RuntimeError):
    """Raised on a non-2xx Orion response (carries status + body)."""

    def __init__(self, status: int, body: str, url: str) -> None:
        super().__init__(f"Orion {status} for {url}: {body[:500]}")
        self.status = status
        self.body = body
        self.url = url


class OrionClient:
    """A thin requests-based Orion client.

    Args:
        base_url: Tenant API root, e.g. ``https://acme.everspot.test/api``.
            Tenant resolution is by domain, so this URL *is* the tenant selector.
        token: Bearer token (from the project's ``token_env_var``).
        user_id: The ``user-id`` header value (the migration user's id).
        timeout: Per-request timeout (seconds).
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        user_id: int,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        session: Optional["requests.Session"] = None,
    ) -> None:
        if requests is None:
            raise RuntimeError("`requests` is required for OrionClient.")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "user-id": str(user_id),
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    # -- low-level ---------------------------------------------------------- #
    def _url(self, resource: str, suffix: str = "") -> str:
        return f"{self.base_url}/{resource.strip('/')}{suffix}"

    def _request(self, method: str, url: str, *, json: Any = None, params: Any = None) -> dict:
        resp = self._session.request(method, url, json=json, params=params, timeout=self.timeout)
        if not resp.ok:
            raise OrionError(resp.status_code, resp.text, url)
        return resp.json() if resp.content else {}

    # -- read --------------------------------------------------------------- #
    def search(
        self,
        resource: str,
        *,
        filters: Optional[Sequence[dict]] = None,
        scopes: Optional[Sequence[dict]] = None,
        sort: Optional[Sequence[dict]] = None,
        search: Optional[dict] = None,
        limit: int = DEFAULT_PAGE_SIZE,
        page: int = 1,
    ) -> dict:
        """``POST /{resource}/search`` with Orion's filter/scope/sort/search DSL.

        Example filter: ``[{"field": "type", "operator": "=", "value": "name_suffix"}]``.
        Returns the raw Orion paginated envelope (``data`` + ``meta`` + ``links``).
        """
        payload: dict[str, Any] = {}
        if filters:
            payload["filters"] = list(filters)
        if scopes:
            payload["scopes"] = list(scopes)
        if sort:
            payload["sort"] = list(sort)
        if search:
            payload["search"] = search
        return self._request(
            "POST",
            self._url(resource, "/search"),
            json=payload,
            params={"limit": limit, "page": page},
        )

    def paginate(
        self,
        resource: str,
        *,
        filters: Optional[Sequence[dict]] = None,
        scopes: Optional[Sequence[dict]] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> Iterator[dict]:
        """Generator yielding every record across all pages of a search.

        Used for dedup paging (customers/properties) and full reference pulls.
        """
        page = 1
        while True:
            envelope = self.search(
                resource, filters=filters, scopes=scopes, limit=page_size, page=page
            )
            rows = envelope.get("data", [])
            yield from rows
            meta = envelope.get("meta", {})
            last_page = meta.get("last_page")
            if last_page is not None:
                if page >= last_page:
                    return
            elif len(rows) < page_size:
                return
            page += 1

    def get(self, resource: str, resource_id: int | str) -> dict:
        """``GET /{resource}/{id}`` → the single record's ``data``."""
        return self._request("GET", self._url(resource, f"/{resource_id}")).get("data", {})

    # -- write -------------------------------------------------------------- #
    def create(self, resource: str, payload: dict) -> dict:
        """``POST /{resource}`` to create one record; returns created ``data``.

        Used by Wave-0b reference-data creation (e.g. missing list_options).
        """
        return self._request("POST", self._url(resource), json=payload).get("data", {})

    def update(self, resource: str, resource_id: int | str, payload: dict) -> dict:
        """``PATCH /{resource}/{id}`` to update one record; returns updated ``data``.

        Used by the idempotent loader: when an external_id already resolves to a tenant
        record, the loader updates it in place instead of creating a duplicate.
        """
        return self._request(
            "PATCH", self._url(resource, f"/{resource_id}"), json=payload
        ).get("data", {})

    def post(self, path: str, payload: dict) -> dict:
        """``POST /{path}`` to a non-resource action endpoint; returns the raw envelope.

        Used for Orion controller actions that are not part of the uniform REST surface,
        e.g. the Attribute engine's idempotent ``attribute-values/batch-upsert`` upsert
        endpoint (resolves attribute values by ``key`` and upserts them — re-running does
        not duplicate). Returns the whole JSON body (the action shapes are non-uniform:
        ``data``/``errors``/``summary``), so the caller inspects what it needs.
        """
        return self._request("POST", self._url(path), json=payload)

    def batch_store(self, resource: str, rows: Sequence[dict]) -> list[dict]:
        """``POST /{resource}/batch`` to create many records in one call.

        Note: Orion batch DB transactions are off by default (plan §2.2 / §6),
        so this is *not* atomic unless ``transactionsAreEnabled`` is turned on for
        the resource — validate upstream.
        """
        result = self._request("POST", self._url(resource, "/batch"), json={"resources": list(rows)})
        return result.get("data", [])
