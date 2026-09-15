"""Caching of road station details, and fetching data for several stations at once."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable, Hashable, Iterable, Mapping
from typing import Any

from .api import DigitrafficError

_LOGGER = logging.getLogger(__name__)

# Digitraffic asks clients not to flood it; a few requests at a time is plenty.
DEFAULT_CONCURRENCY = 4


class DetailCache[K: Hashable]:
    """Details of stations or cameras, such as their names, fetched once per id.

    Details rarely change, so each is kept for `ttl_seconds`. A failed lookup
    isn't cached, so the next update tries again. Shared by every feed.
    """

    def __init__(
        self,
        name: str,
        fetch: Callable[[K], Awaitable[dict[str, Any]]],
        ttl_seconds: float = 24 * 3600,
        concurrency: int = DEFAULT_CONCURRENCY,
    ) -> None:
        self._name = name
        self._fetch = fetch
        self._ttl = ttl_seconds
        self._concurrency = concurrency
        self._entries: dict[K, tuple[dict[str, Any], float]] = {}
        self._lock = asyncio.Lock()

    def get(self, key: K) -> dict[str, Any] | None:
        entry = self._entries.get(key)
        return entry[0] if entry else None

    async def ensure(self, keys: Iterable[K]) -> None:
        """Makes sure details are cached for the given ids."""
        async with self._lock:
            now = time.monotonic()
            missing = [key for key in dict.fromkeys(keys) if self._is_stale(key, now)]
            results = await fetch_each(missing, self._fetch, self._concurrency, self._name)
            fetched_at = time.monotonic()
            for key, value in results.items():
                self._entries[key] = (value, fetched_at)

    def _is_stale(self, key: K, now: float) -> bool:
        entry = self._entries.get(key)
        return entry is None or now - entry[1] > self._ttl


async def fetch_each[K: Hashable, V](
    keys: Iterable[K],
    fetch: Callable[[K], Awaitable[V]],
    concurrency: int = DEFAULT_CONCURRENCY,
    name: str = "item",
) -> dict[K, V]:
    """Fetches every key, a few at a time. Keys whose fetch fails are left out."""
    semaphore = asyncio.Semaphore(concurrency)
    results: dict[K, V] = {}

    async def load(key: K) -> None:
        async with semaphore:
            try:
                results[key] = await fetch(key)
            except DigitrafficError as err:
                _LOGGER.debug("Fetching %s %s failed: %s", name, key, err)

    await asyncio.gather(*(load(key) for key in keys))
    return results


def details_name(details: Mapping[str, Any] | None, language: str) -> str | None:
    """A station's or camera's name in the chosen language, from its details: "Road 6 Lappeenranta, Kärki"."""
    names = ((details or {}).get("properties") or {}).get("names") or {}
    return names.get(language) or names.get("fi")
