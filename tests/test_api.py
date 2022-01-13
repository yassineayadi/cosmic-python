from conftest import make_test_batch_and_order_item, make_test_product, make_test_sku
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
