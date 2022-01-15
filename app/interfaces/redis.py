import pickle

import redis
from core import events


class RedisClient(redis.Redis):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_event(self, event: events.Event) -> None:
        event_id = str(event.uuid.hex)
        event_s = pickle.dumps(event)
        self.set(event_id, event_s)

    def get_event(self, event_id: str) -> events.Event:
        event_s = self.get(event_id)
        event = pickle.loads(event_s)
        return event


def get_redis_client() -> RedisClient:
    client = RedisClient(host="localhost", port=6379, db=0)
    return client
