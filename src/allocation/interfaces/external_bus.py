import pickle
from typing import Type

import redis

from allocation import core
from allocation.config import get_redis_config
from allocation.core import events


class RedisClient(redis.Redis):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subscription = self.pubsub()
        self.active_subscriptions = set()

    def publish_channel_message(self, message: core.Message) -> None:
        channel = message.name
        event_data = pickle.dumps(message)
        self.publish(channel, event_data)

    def subscribe_to_channel(self, message_type: Type[core.Message]):
        channel = message_type.__name__
        self.subscription.subscribe(channel)
        self.active_subscriptions.add(channel)

    def get_channel_message(self, message_type: Type[core.Message]):
        channel = message_type.__name__
        if channel not in self.active_subscriptions:
            raise ConnectionError(f"Currently not subscribed to channel {channel}.")

        redis_message = self.subscription.get_message()
        if redis_message:
            message = parse_redis_message(redis_message)
            if isinstance(message, message_type):
                return message


def create_redis_client() -> RedisClient:
    client = RedisClient(**get_redis_config())
    return client


def parse_redis_message(message: dict) -> events.Event:
    message = message.copy()
    if message["type"] == "message":
        data = message.get("data")
        event = pickle.loads(data)
        return event
