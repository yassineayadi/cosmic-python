import datetime

import pytest

from allocation.repositories import InvalidSKU
from conftest import (
    make_test_order_item,
    make_test_product,
    make_test_sku,
    make_test_sku_product_and_batch,
    make_test_sku_product_and_order_item,
)

from allocation import services
from allocation.core import commands, domain, events
from allocation.core.commands import Allocate, CreateOrderItem, CreateProductCommand
from allocation.interfaces.database.db import session_factory
from allocation.unit_of_work import UnitOfWork


def test_create_product_command():
    sku = domain.create_sku("SKU")
    cmd = CreateProductCommand(sku)
    uow = UnitOfWork(session_factory)
    services.create_product(cmd, uow)
    [event] = list(uow.collect_new_messages())
    assert isinstance(event, events.ProductCreated)


def test_update_product_command():

    with UnitOfWork() as uow:
        product = make_test_product()
        uow.products.add(product)
        sku_id = product.sku.uuid

    cmd = commands.UpdateProduct(sku_id, "SKU-UPDATED-NAME")
    services.update_product(cmd, UnitOfWork())

    with UnitOfWork() as uow:
        product = uow.products.get(sku_id)
        assert product.sku.name == "SKU-UPDATED-NAME"


def test_discard_product_command():

    with UnitOfWork() as uow:
        product = make_test_product()
        uow.products.add(product)
        sku_id = product.sku.uuid

    cmd = commands.DiscardProduct(sku_id)
    services.discard_product(cmd, UnitOfWork())

    with pytest.raises(InvalidSKU):
        with UnitOfWork() as uow:
            uow.products.get(sku_id)


def test_create_order_item_command():
    sku = make_test_sku()
    cmd = CreateOrderItem(sku_id=sku.uuid, quantity=7)
    assert isinstance(cmd, CreateOrderItem) is True


def test_update_order_item_command():
    with UnitOfWork() as uow:
        sku, product, order_item = make_test_sku_product_and_order_item()
        product.register_order_item(order_item)
        uow.products.add(product)
        sku_id, order_item_id = sku.uuid, order_item.uuid

    cmd = commands.UpdateOrderItem(sku_id, order_item_id, 40)
    services.update_order_item(cmd, UnitOfWork())

    with UnitOfWork() as uow:
        order_item = next(
            oi for oi in uow.products.get_all_order_items() if oi.uuid == order_item_id
        )
        assert order_item.quantity == 40


def test_discard_order_item_command():
    with UnitOfWork() as uow:
        sku, product, order_item = make_test_sku_product_and_order_item()
        product.register_order_item(order_item)
        uow.products.add(product)
        sku_id, order_item_id = sku.uuid, order_item.uuid

    cmd = commands.DiscardOrderItem(sku_id, order_item_id)
    services.discard_order_item(cmd, UnitOfWork())

    with UnitOfWork() as uow:
        product = uow.products.get(sku_id)
        with pytest.raises(StopIteration):
            next(oid for oid in product.order_items if oid == order_item_id)


def test_idempotency_of_discard_order_item_command():
    with UnitOfWork() as uow:
        sku, product, order_item = make_test_sku_product_and_order_item()
        product.register_order_item(order_item)
        uow.products.add(product)
        sku_id, order_item_id = sku.uuid, order_item.uuid

    cmd_1 = commands.DiscardOrderItem(sku_id, order_item_id)
    cmd_2 = commands.DiscardOrderItem(sku_id, order_item_id)

    services.discard_order_item(cmd_1, UnitOfWork())
    services.discard_order_item(cmd_2, UnitOfWork())


def test_create_order_item_handler():
    sku = make_test_sku()
    cmd = CreateOrderItem(sku_id=sku.uuid, quantity=7)
    uow = UnitOfWork(session_factory)
    services.create_product(CreateProductCommand(sku), uow)
    services.create_order_item(cmd, uow)
    event = next(event for event in uow.collect_new_messages())
    assert isinstance(event, events.OrderItemCreated)


def test_create_batch_command():
    with UnitOfWork() as uow:
        product = make_test_product()
        uow.products.add(product)
        sku_id = product.sku.uuid

    cmd = commands.CreateBatch(sku_id, 13, datetime.datetime.today())
    batch_id = services.create_batch(cmd, UnitOfWork())

    with UnitOfWork() as uow:
        created_batch = next(
            b for b in uow.products.get_all_batches() if b.uuid == batch_id
        )
        assert created_batch


def test_change_batch_command():
    with UnitOfWork() as uow:
        sku, product, batch = make_test_sku_product_and_batch()
        product.register_batch(batch)
        uow.products.add(product)
        sku_id, batch_id = sku.uuid, batch.uuid

    cmd = commands.ChangeBatchQuantity(sku_id, batch_id, 40)
    services.change_batch_quantity(cmd, UnitOfWork())

    with UnitOfWork() as uow:
        batch = next(b for b in uow.products.get_all_batches() if b.uuid == batch_id)
        assert batch.quantity == 40


def test_delete_batch_command():
    with UnitOfWork() as uow:
        sku, product, batch = make_test_sku_product_and_batch()
        product.register_batch(batch)
        uow.products.add(product)
        sku_id, batch_id = sku.uuid, batch.uuid

    cmd = commands.DiscardBatch(sku_id, batch_id)
    services.discard_batch(cmd, UnitOfWork())

    with UnitOfWork() as uow:
        with pytest.raises(StopIteration):
            next(b for b in uow.products.get_all_batches() if b.uuid == batch_id)


def test_change_number_of_allocated_items_on_batch_quantity_change():
    with UnitOfWork(session_factory) as uow:
        sku, product, batch = make_test_sku_product_and_batch()
        order_items = make_test_order_item(sku), make_test_order_item(sku)
        uow.products.add(product)
        [product.allocate(o) for o in order_items]

        sku_id = sku.uuid
        batch_id = batch.uuid
        assert len(batch.allocated_order_items) == 2

    cmd = commands.ChangeBatchQuantity(sku_id, batch_id, 15)
    services.change_batch_quantity(cmd, UnitOfWork(session_factory))

    with UnitOfWork(session_factory) as uow:
        product = uow.products.get(sku_id)
        batch = product.batches.pop()
        assert len(batch.allocated_order_items) == 1


def test_allocate_handler():
    with UnitOfWork(session_factory) as uow:
        sku, product, _ = make_test_sku_product_and_batch()
        uow.products.add(product)
        sku_id = sku.uuid

    order_item_id = services.create_order_item(
        CreateOrderItem(sku_id=sku_id, quantity=10), uow
    )
    services.allocate(Allocate(sku_id=sku_id, order_item_id=order_item_id), uow)
    [event] = list(uow.collect_new_messages())
    assert isinstance(event, events.OrderItemAllocated)
