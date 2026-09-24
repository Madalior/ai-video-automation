"""
EventBus — Real-Time Pipeline Event Hub
=======================================
Thread-safe singleton event emitter for real-time progress tracking.
Provides pub/sub callbacks and FIFO queues for Server-Sent Events (SSE).
"""

import time
import queue
import threading
from typing import Callable, Optional


class PipelineEvent:
    """Represents a single discrete pipeline event."""

    def __init__(self, event_id: int, event_type: str, data: dict, timestamp: float = None):
        self.id = event_id
        self.type = event_type
        self.data = data or {}
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class EventBus:
    """Singleton event bus with in-memory ring buffer and SSE listener queues."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._init_bus()
            return cls._instance

    def _init_bus(self):
        self._subscribers: dict[str, list[Callable]] = {}
        self._all_subscribers: list[Callable] = []
        self._events: list[PipelineEvent] = []
        self._event_counter = 0
        self._event_lock = threading.Lock()
        self._listeners_lock = threading.Lock()
        self._queues: list[queue.Queue] = []

    def emit(self, event_type: str, data: dict = None) -> PipelineEvent:
        """Emit an event to all subscribers and SSE listener queues."""
        if data is None:
            data = {}

        with self._event_lock:
            self._event_counter += 1
            event = PipelineEvent(self._event_counter, event_type, data)
            self._events.append(event)
            if len(self._events) > 1000:
                self._events.pop(0)

        with self._listeners_lock:
            # Deliver to SSE queues
            for q in list(self._queues):
                try:
                    q.put_nowait(event)
                except Exception:
                    pass

            callbacks = list(self._subscribers.get(event_type, [])) + list(self._all_subscribers)

        for cb in callbacks:
            try:
                cb(event)
            except Exception as e:
                print(f"[EVENT_BUS] Callback error for {event_type}: {e}")

        return event

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to a specific event type, or '*' for all."""
        with self._listeners_lock:
            if event_type == "*":
                self._all_subscribers.append(callback)
            else:
                self._subscribers.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """Remove an existing subscription."""
        with self._listeners_lock:
            if event_type == "*" and callback in self._all_subscribers:
                self._all_subscribers.remove(callback)
            elif event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def register_queue(self) -> queue.Queue:
        """Register a new consumer queue (e.g. for an active SSE connection)."""
        q = queue.Queue(maxsize=200)
        with self._listeners_lock:
            self._queues.append(q)
        return q

    def unregister_queue(self, q: queue.Queue):
        """Remove a consumer queue when connection closes."""
        with self._listeners_lock:
            if q in self._queues:
                self._queues.remove(q)

    def get_events(self, since_id: int = 0) -> list[dict]:
        """Fetch historical buffered events since a given event ID."""
        with self._event_lock:
            return [e.to_dict() for e in self._events if e.id > since_id]


# Global singleton instance
bus = EventBus()
event_bus = bus
