"""
Central Redis-backed state store.
"""
from typing import List, Dict, Any
import json
import os
import asyncio
import redis.asyncio as redis


class StateStore:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis = redis.from_url(self.redis_url, decode_responses=True)
        self._lock = asyncio.Lock()

        # Config flags
        self.auto_heal: bool = True
        self.alert_channels: List[str] = ["slack", "email"]

        # Connected websocket clients
        self.ws_clients: List[Any] = []

    async def _get_list(self, key: str, start: int = 0, end: int = -1) -> List[dict]:
        """Get list from Redis, parsing JSON items."""
        items = await self.redis.lrange(key, start, end)
        return [json.loads(item) for item in items]

    async def _add_to_list(self, key: str, item: dict, maxlen: int):
        """Add item to Redis list with maxlen constraint."""
        await self.redis.lpush(key, json.dumps(item))
        await self.redis.ltrim(key, 0, maxlen - 1)

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

    def get_metrics(self, limit: int = 60) -> List[dict]:
        """Get last N metrics (synchronous for compatibility)."""
        try:
            # Create a new event loop if one doesn't exist
            try:
                loop = asyncio.get_running_loop()
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

    def get_logs(self, limit: int = 100, service: str = None, level: str = None) -> List[dict]:
        """Get filtered logs (synchronous for compatibility)."""
        try:
            try:
                loop = asyncio.get_running_loop()
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

    def get_incidents(self, limit: int = 50) -> List[dict]:
        """Get last N incidents (synchronous for compatibility)."""
        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._get_list("incidents", 0, limit - 1))
                    return future.result(timeout=5.0)
            except RuntimeError:
                return asyncio.run(self._get_list("incidents", 0, limit - 1))
        except Exception:
            return []

    def get_healing_actions(self, limit: int = 50) -> List[dict]:
        """Get last N healing actions (synchronous for compatibility)."""
        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._get_list("healing_actions", 0, limit - 1))
                    return future.result(timeout=5.0)
            except RuntimeError:
                return asyncio.run(self._get_list("healing_actions", 0, limit - 1))
        except Exception:
            return []

    def get_alerts(self, limit: int = 50) -> List[dict]:
        """Get last N alerts (synchronous for compatibility)."""
        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._get_list("alerts", 0, limit - 1))
                    return future.result(timeout=5.0)
            except RuntimeError:
                return asyncio.run(self._get_list("alerts", 0, limit - 1))
        except Exception:
            return []

    def get_summary(self) -> dict:
        """Get system summary (synchronous for compatibility)."""
        try:
            try:
                loop = asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._get_list("incidents", 0, 9))
                    incidents = future.result(timeout=5.0)
            except RuntimeError:
                incidents = asyncio.run(self._get_list("incidents", 0, 9))
            
            critical = sum(1 for inc in incidents if inc.get("severity") == "CRITICAL")
            return {
                "healthy": critical == 0,
                "incidents": len(incidents),
                "auto_heal": self.auto_heal,
            }
        except Exception:
            return {"healthy": False, "incidents": 0, "auto_heal": self.auto_heal}


# Global instance
store = StateStore()
