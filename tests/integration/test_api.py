import datetime

import serializers
import services
from conftest import (
    make_test_batch,
    make_test_batch_and_order_item,
    make_test_product,
    make_test_sku,
)
from core.commands import CreateProductCommand
from flask.testing import FlaskClient

from app.interfaces import session_factory
from app.repositories import UnitOfWork
from app.serializers import SKUSchema


def test_index(client: FlaskClient):
    rv = client.get("/")
    assert b"Index" in rv.data


def test_list_skus(client: FlaskClient):
    with UnitOfWork(session_factory) as uow:
        test_sku_1 = make_test_sku()
        test_sku_2 = make_test_sku()
        test_pro_1 = make_test_product(test_sku_1)
        test_pro_2 = make_test_product(test_sku_2)
        uow.products.add_all([test_pro_1, test_pro_2])
        sku_refs = [sku.uuid for sku in [test_sku_2, test_sku_1]]

    response = client.get("/skus")

    retrieved_skus = SKUSchema().load(response.json, many=True)
    retrieved_skus_refs = [sku.uuid for sku in retrieved_skus]
    for sku_ref in sku_refs:
        assert sku_ref in retrieved_skus_refs


def test_create_batch(client: FlaskClient):
    with UnitOfWork(session_factory) as uow:
        test_sku_1 = make_test_sku()
        product = make_test_product(sku=test_sku_1)
        uow.products.add(product)
        sku_id = product.sku_id

    data = {
        "sku_id": sku_id,
        "eta": datetime.datetime.now().timestamp(),
        "quantity": 20,
    }

    client.post("/batch/create", json=data)
    with UnitOfWork(session_factory) as uow:
        product = uow.products.get(sku_id)
        assert len(product.batches) == 1


def test_redirect_on_create_batch(client: FlaskClient):
    with UnitOfWork(session_factory) as uow:
        test_sku = make_test_sku()
        product = make_test_product(sku=test_sku)
        uow.products.add(product)
        sku_id = product.sku_id

    data = {
        "sku_id": sku_id,
        "eta": datetime.datetime.now().timestamp(),
        "quantity": 20,
    }
    response = client.post("batch/create", json=data, follow_redirects=True)
    with UnitOfWork(session_factory) as uow:
        response_batch = response.json
        product = uow.products.get(sku_id)
        saved_batch = serializers.BatchSchema().dump(product.batches.pop())
        assert response_batch == saved_batch


def test_get_batch(client: FlaskClient):

    sku = make_test_sku()
    sku_id = sku.uuid
    cmd = CreateProductCommand(sku)
    today = datetime.datetime.now()
    today_s = today.timestamp()
    services.create_product(cmd, UnitOfWork(session_factory))

    with UnitOfWork(session_factory) as uow:
        product = uow.products.get(sku_id)
        batch = make_test_batch(product.sku, batch_qty=10, eta=datetime.datetime.now())
        product.register_batch(batch)
        batch_id = batch.uuid
        batch_data = serializers.BatchSchema().dump(batch)

    response = client.get(f"batch/{batch_id!s}")
    response_data = response.json
    assert batch_data == response_data


def test_allocation_one_matching_batch_order_item_pair(client: FlaskClient):

    with UnitOfWork(session_factory) as uow:
        sku = make_test_sku()
        batch, order_item = make_test_batch_and_order_item(sku, 20, 2)
        product = make_test_product(sku, batches={batch})
        uow.products.add(product=product)
        product_id = sku.uuid
        data = order_item.to_dict()

    client.post("/allocate", json=data)

    with UnitOfWork(session_factory) as uow:
        product = uow.products.get_by_sku_uuid(product_id)
        batch = product.batches.pop()
        assert batch.available_quantity == 18
