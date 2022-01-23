import random
import threading
import time
import traceback
from datetime import date, timedelta
from typing import List
from uuid import UUID

import pytest
import sqlalchemy.exc
from conftest import (
    make_test_batch,
    make_test_batch_and_order_item,
    make_test_order_item,
    make_test_product,
    make_test_sku,
    make_test_sku_product_and_batch,
)

from allocation.core.domain import AllocationError
from allocation.interfaces.database.db import session_factory
from allocation.unit_of_work import UnitOfWork


class TestUnitOfWork:
    def test_create_uow(self):
        uow = UnitOfWork(session_factory)
        assert isinstance(uow, UnitOfWork)

    def test_successful_open_products_on_enter(self):
        uow = UnitOfWork(session_factory)

        with uow as uow:
            assert hasattr(uow, "products")

    def test_successful_close_products_on_exit(self):
        uow = UnitOfWork(session_factory)
        with uow:
            pass


def try_to_register_batch(product_id: UUID, exceptions: List[Exception]):
    try:
        with UnitOfWork(session_factory) as uow:
            product = uow.products.get(product_id)
            batch = make_test_batch(sku=product.sku)
            product.register_batch(batch)
            time.sleep(0.2)
            print(product.version_number)
            uow.session.commit()
    except Exception as e:  # pylint:disable=broad-except
        exceptions.append(e)
        raise Exception("Exception") from e


def test_save_order_item():
    with UnitOfWork() as uow:
        sku_1 = make_test_sku()
        product_1, order_item_1 = make_test_product(sku_1), make_test_order_item(sku_1)
        product_1.register_order_item(order_item_1)
        uow.products.add(product_1)
        sku_id, order_item_id = product_1.sku_id, order_item_1.uuid

    with UnitOfWork() as uow:
        retrieved_order_item = uow.products.get(sku_id).order_items.pop()
        assert retrieved_order_item.uuid == order_item_id


def try_to_allocate(product_id: UUID, exceptions: List[Exception]):
    try:
        with UnitOfWork(session_factory) as uow:
            product = uow.products.get(product_id)
            qty = random.randint(10, 17)
            order_item = make_test_order_item(product.sku, qty)
            product.allocate(order_item)
            time.sleep(0.2)
            # print(product.version_number)
    except Exception as err:  # pylint:disable=broad-except
        # print(err)
        print(traceback.format_exc())
        exceptions.append(err)


def test_race_condition_on_order_item_allocation():
    with UnitOfWork(session_factory) as uow:
        _, product, _ = make_test_sku_product_and_batch()
        uow.products.add(product)
        product_id = product.sku_id

    exceptions: List[Exception] = []
    try_to_allocate_1 = lambda: try_to_allocate(product_id, exceptions)
    try_to_allocate_2 = lambda: try_to_allocate(product_id, exceptions)

    t1 = threading.Thread(target=try_to_allocate_1)
    t2 = threading.Thread(target=try_to_allocate_2)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert len(exceptions) == 1
    for exc in exceptions:
        assert isinstance(exc, sqlalchemy.exc.OperationalError)


def test_insert_order_item_multiple_times():
    with pytest.raises(AllocationError):
        with UnitOfWork() as uow:
            sku = make_test_sku()
            batch, order_item = make_test_batch_and_order_item(sku, 20, 10)
            product = make_test_product(sku)
            uow.products.add(product)
            product.register_batch(batch)
            product.allocate(order_item)
            product.allocate(order_item)


def test_create_and_register_batch():
    with UnitOfWork() as uow:
        _, product, batch = make_test_sku_product_and_batch()
        uow.products.add(product)
        product.register_batch(batch)
        batch_id = batch.uuid

    with UnitOfWork() as uow:
        product = uow.products.list().pop()
        retrieved_batch = next(b for b in product.batches)
        assert batch_id == retrieved_batch.uuid


def test_create_allocate_and_retrieve_same_batches():
    with UnitOfWork() as uow:
        sku = make_test_sku()
        allocation_batch, order_item = make_test_batch_and_order_item(sku, 20, 2)
        product = make_test_product(sku)
        uow.products.add(product)
        product.register_batch(allocation_batch)
        product.allocate(order_item)
        uow.commit()

        product = uow.products.get(product.sku_id)
        retrieved_batch = product.batches.pop()

        assert retrieved_batch == allocation_batch


def test_increment_product_version_number():
    with UnitOfWork() as uow:
        _, product_1, batch_1 = make_test_sku_product_and_batch()
        uow.products.add(product_1)
        sku_uuid = product_1.sku_id
        assert product_1.version_number == 0

    with UnitOfWork() as uow:
        product_1 = uow.products.get(sku_uuid)
        batch_2 = make_test_batch(product_1.sku, 30, date.today() + timedelta(days=5))
        product_1.register_batch(batch_2)

        assert product_1.version_number == 1


def test_get_all_batches():
    with UnitOfWork() as uow:
        sku1 = make_test_sku()
        batches_a = batch1, batch2, batch3 = (
            make_test_batch(sku1, 10),
            make_test_batch(sku1, 20),
            make_test_batch(sku1, 30),
        )
        product1 = make_test_product(sku1, {batch1, batch2, batch3})
        uow.products.add(product1)
        sku2 = make_test_sku()
        batches_b = batch4, batch5, batch6 = (
            make_test_batch(sku2, 10),
            make_test_batch(sku2, 20),
            make_test_batch(sku2, 30),
        )
        product2 = make_test_product(sku2, {batch4, batch5, batch6})
        uow.products.add(product2)
        batchrefs_a = {batch.uuid for batch in batches_a}
        batchrefs_b = {batch.uuid for batch in batches_b}
        batchrefs = batchrefs_a.union(batchrefs_b)

    with UnitOfWork() as uow:
        retrieved_batchrefs = {b.uuid for b in uow.products.get_all_batches()}
        assert batchrefs.intersection(retrieved_batchrefs) == batchrefs


def test_delete_order_item():
    with UnitOfWork(session_factory) as uow:
        sku = make_test_sku()
        product = make_test_product(sku)
        order_item = make_test_order_item(sku)
        uow.products.add(product)
        product.order_items.add(order_item)
        sku_id = product.sku_id
        order_item_id = order_item.uuid

    with UnitOfWork(session_factory) as uow:
        product = uow.products.get(sku_id)
        order_item = product.order_items.pop()
        assert order_item.uuid == order_item_id


def test_unit_of_work_exception_handling():
    class CustomError(Exception):
        pass

    with pytest.raises(CustomError):
        with UnitOfWork(session_factory):
            raise CustomError


def test_unit_of_work_rollback_on_error():
    class CustomError(Exception):
        pass

    with pytest.raises(CustomError):
        with UnitOfWork() as uow:
            product = make_test_product(make_test_sku())
            sku_id = product.sku_id
            uow.products.add(product)
            raise CustomError

    with UnitOfWork() as uow:
        product = uow.products.get(sku_id)
        assert product is None
