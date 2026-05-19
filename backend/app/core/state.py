"""
Central Redis-backed state store.
"""
import asyncio
import json
import os
from typing import Any

import redis.asyncio as redis


class StateStore:
    def __init__(self):
        password = os.getenv("REDIS_PASSWORD", "").strip()
        base_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_url = base_url if not password else base_url.replace("redis://", f"redis://:{password}@")
        # Create redis client; if Redis is unavailable we'll fallback to an in-memory store.
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            self._use_redis = True
        except Exception:
            self.redis = None
            self._use_redis = False
        self._lock = asyncio.Lock()

        # Config flags
        self.auto_heal: bool = True
        self.alert_channels: list[str] = ["slack", "email"]

        # Connected websocket clients
        self.ws_clients: list[Any] = []
        # In-memory fallback lists (used if Redis is not reachable)
        from collections import deque

        self._metrics_list: deque = deque(maxlen=300)
        self._logs_list: deque = deque(maxlen=1000)
        self._incidents_list: deque = deque(maxlen=200)
        self._healing_list: deque = deque(maxlen=200)
        self._alerts_list: deque = deque(maxlen=200)

    async def _get_list(self, key: str, start: int = 0, end: int = -1) -> list[dict]:
        """Get list from Redis, parsing JSON items."""
        if self._use_redis and self.redis is not None:
            try:
                items = await self.redis.lrange(key, start, end)
                return [json.loads(item) for item in items]
            except Exception:
                # Fall through to in-memory fallback
                self._use_redis = False

        # In-memory fallback
        if key == "metrics":
            return list(self._metrics_list)[start : (end + 1 if end != -1 else None)]
        if key == "logs":
            return list(self._logs_list)[start : (end + 1 if end != -1 else None)]
        if key == "incidents":
            return list(self._incidents_list)[start : (end + 1 if end != -1 else None)]
        if key == "healing_actions":
            return list(self._healing_list)[start : (end + 1 if end != -1 else None)]
        if key == "alerts":
            return list(self._alerts_list)[start : (end + 1 if end != -1 else None)]
        return []

    async def _add_to_list(self, key: str, item: dict, maxlen: int):
        """Add item to Redis list with maxlen constraint."""
        if self._use_redis and self.redis is not None:
            try:
                await self.redis.lpush(key, json.dumps(item))
                await self.redis.ltrim(key, 0, maxlen - 1)
                return
            except Exception:
                # Disable redis use and fall back to in-memory
                self._use_redis = False

        # In-memory fallback
        if key == "metrics":
            self._metrics_list.appendleft(item)
        elif key == "logs":
            self._logs_list.appendleft(item)
        elif key == "incidents":
            self._incidents_list.appendleft(item)
        elif key == "healing_actions":
            self._healing_list.appendleft(item)
        elif key == "alerts":
            self._alerts_list.appendleft(item)

    async def add_metric(self, point: dict):
        async with self._lock:
            await self._add_to_list("metrics", point, 300)

    async def add_log(self, entry: dict):
        async with self._lock:
            await self._add_to_list("logs", entry, 1000)

    async def add_incident(self, inc: dict):
        async with self._lock:
            await self._add_to_list("incidents", inc, 200)

    async def update_incident(self, inc_id: str, updates: dict):
        async with self._lock:
            incidents = await self._get_list("incidents")
            for i, inc in enumerate(incidents):
                if inc["id"] == inc_id:
                    updated_inc = {**inc, **updates}
                    incidents[i] = updated_inc
                    break
            else:
                return

            # Clear and repopulate the list
            await self.redis.delete("incidents")
            for inc in reversed(incidents):
                await self.redis.lpush("incidents", json.dumps(inc))

    async def add_healing_action(self, action: dict):
        async with self._lock:
            await self._add_to_list("healing_actions", action, 200)

    async def add_alert(self, alert: dict):
        async with self._lock:
            await self._add_to_list("alerts", alert, 200)

    def get_metrics(self, limit: int = 60) -> list[dict]:
        """Get last N metrics (synchronous for compatibility)."""
        try:
            # Create a new event loop if one doesn't exist
            try:
                asyncio.get_running_loop()
                # If we're in an async context, create a task to run in background
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._get_list("metrics", 0, limit - 1))
                    return future.result(timeout=5.0)
            except RuntimeError:
                # No running loop, we can create one
                return asyncio.run(self._get_list("metrics", 0, limit - 1))
        except Exception:
            return []

    def get_logs(self, limit: int = 100, service: str = None, level: str = None) -> list[dict]:
        """Get filtered logs (synchronous for compatibility)."""
        try:
            try:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._get_list("logs", 0, limit - 1))
                    logs = future.result(timeout=5.0)
            except RuntimeError:
                logs = asyncio.run(self._get_list("logs", 0, limit - 1))

            if service:
                logs = [log for log in logs if log.get("service") == service]
            if level:
                logs = [log for log in logs if log.get("level") == level]
            return logs
        except Exception:
            return []

    def get_incidents(self, limit: int = 50) -> list[dict]:
        """Get last N incidents (synchronous for compatibility)."""
        try:
            try:
                asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._get_list("incidents", 0, limit - 1))
                    return future.result(timeout=5.0)
            except RuntimeError:
                return asyncio.run(self._get_list("incidents", 0, limit - 1))
        except Exception:
            return []

    def get_alerts(self, limit: int = 50) -> list[dict]:
        """Get last N alerts (synchronous for compatibility)."""
        try:
            try:
                asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._get_list("alerts", 0, limit - 1))
                    return future.result(timeout=5.0)
            except RuntimeError:
                return asyncio.run(self._get_list("alerts", 0, limit - 1))
        except Exception:
            return []


# Global instance
store = StateStore()
