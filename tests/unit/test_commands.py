import services
from conftest import (
    make_test_order_item,
    make_test_sku,
    make_test_sku_product_and_batch,
)
from core import commands
from interfaces import session_factory
from repositories import UnitOfWork

from app.core import domain, events
from app.core.commands import AllocateCommand, CreateOrderItem, CreateProductCommand


def test_create_order_item_command():
    sku = make_test_sku()
    cmd = CreateOrderItem(sku_id=sku.uuid, quantity=7)
    assert isinstance(cmd, CreateOrderItem) is True


def test_create_order_item_handler():
    sku = make_test_sku()
    cmd = CreateOrderItem(sku_id=sku.uuid, quantity=7)
    uow = UnitOfWork(session_factory)
    services.create_product(CreateProductCommand(sku), uow)
    services.create_order_item(cmd, uow)
    [event] = [event for event in uow.collect_new_messages()]
    assert isinstance(event, events.OrderItemCreated)


def test_create_product_command():
    sku = domain.create_sku("SKU")
    cmd = CreateProductCommand(sku=sku)
    uow = UnitOfWork(session_factory)
    services.create_product(cmd, uow)
    [event] = list(uow.collect_new_messages())
    assert isinstance(event, events.ProductCreated)


def test_allocate_handler():
    with UnitOfWork(session_factory) as uow:
        sku, product, _ = make_test_sku_product_and_batch()
        uow.products.add(product)
        sku_id = sku.uuid

    order_item_id = services.create_order_item(
        CreateOrderItem(sku_id=sku_id, quantity=10), uow
    )
    services.allocate(
        AllocateCommand(sku_id=sku_id, order_item_id=order_item_id, quantity=10), uow
    )
    [event] = list(uow.collect_new_messages())
    assert isinstance(event, events.OrderItemAllocated)


def test_change_batch_quantity_command():
    with UnitOfWork(session_factory) as uow:
        sku, product, batch = make_test_sku_product_and_batch()
        order_items = make_test_order_item(sku), make_test_order_item(sku)
        uow.products.add(product)
        [product.register_order_item(o) for o in order_items]
        [product.allocate(o) for o in order_items]

        sku_id = sku.uuid
        batch_id = batch.uuid
        assert len(batch.allocated_order_items) == 2

    cmd = commands.ChangeBatchQuantity(sku_id, batch_id, 15)
    batch_id = services.change_batch_quantity(cmd, UnitOfWork(session_factory))

    with UnitOfWork(session_factory) as uow:
        product = uow.products.get(sku_id)
        batch = product.batches.pop()
        assert len(batch.allocated_order_items) == 1
