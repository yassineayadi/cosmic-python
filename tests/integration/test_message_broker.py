from interfaces import session_factory
from repositories import UnitOfWork

from app import services
from app.core import events
from app.interfaces.redis import get_redis_client
from tests.conftest import (
    make_test_batch,
    make_test_sku,
    make_test_sku_product_and_batch,
)


def test_redis_connection():
    client = get_redis_client()
    client.set("foo", "bar")
    assert client.get("foo") == b"bar"


def test_post_event_on_redis_broker():
    client = get_redis_client()
    batch = make_test_batch(make_test_sku())
    event = events.BatchQuantityChanged(batch.uuid, 10)
    event_id = str(event.uuid.hex)
    client.set_event(event)

    redis_event = client.get_event(event_id)
    assert event == redis_event


def test_publish_event_to_redis_channel_via_handler():
    batch = make_test_batch(make_test_sku())
    event = events.BatchQuantityChanged(batch.uuid, 10)
    services.publish_event_to_external_broker(event)


def test_initiate_command_from_external_event():
    with UnitOfWork(session_factory) as uow:
        _, product, _ = make_test_sku_product_and_batch()
        uow.products.add(product)

    client = get_redis_client()
    # subcription = client.pubsub()
    # subcription.subscribe(events.BatchQuantityChanged.__name__)
    #
