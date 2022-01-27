import time

from conftest import make_test_order_item, make_test_sku_product_and_batch
from flask.testing import FlaskClient

from allocation.core import events
from allocation.interfaces.external_bus import create_redis_client
from allocation.unit_of_work import UnitOfWork


def test_allocate_via_api_and_retrieve_allocated_event_from_external_bus(
    client: FlaskClient,
):
    redis_client = create_redis_client()
    redis_client.subscribe_to_channel(events.OrderItemAllocated)
    with UnitOfWork() as uow:
        sku, product, _ = make_test_sku_product_and_batch()
        order_item = make_test_order_item(sku)
        product.register_order_item(order_item)
        uow.products.add(product)
        sku_id = sku.uuid
        order_item_id = order_item.uuid

    data = {"order_item_id": order_item_id, "sku_id": sku_id}

    response = client.post("/allocate", json=data)
    print(response)

    while True:
        message = redis_client.get_channel_message(events.OrderItemAllocated)
        if message:
            assert isinstance(message, events.OrderItemAllocated)
            break
        time.sleep(0.5)
