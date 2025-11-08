from datetime import datetime
from collections import deque
from typing import List, Literal, Optional
from app.models import PowerEvent


class EventsService:
    def __init__(self, max_events: int = 100):
        self.events: deque = deque(maxlen=max_events)
    
    def add_event(
        self,
        event_type: Literal["shed", "restore", "alert", "warning"],
        message: str,
        array_id: Optional[str] = None,
        led_id: Optional[str] = None,
        details: Optional[dict] = None
    ):
        event = PowerEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            array_id=array_id,
            led_id=led_id,
            message=message,
            details=details or {}
        )
        self.events.appendleft(event)
        return event
    
    def get_recent_events(self, limit: int = 50) -> List[PowerEvent]:
        return list(self.events)[:limit]
    
    def clear(self):
        self.events.clear()
