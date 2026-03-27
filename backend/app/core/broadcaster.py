"""
Simple WebSocket broadcaster.
Maintains a set of active connections and fans out messages.
"""
import json
from typing import Set
from fastapi import WebSocket

_connections: Set[WebSocket] = set()


def register(ws: WebSocket):
    _connections.add(ws)


def unregister(ws: WebSocket):
    _connections.discard(ws)


async def broadcast(payload: dict):
    dead = set()
    msg = json.dumps(payload)
    for ws in list(_connections):
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _connections.discard(ws)
