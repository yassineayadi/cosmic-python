import json
import unittest

from flask.testing import FlaskClient
from flask_unittest import ClientTestCase
from test_domain import make_test_batch_and_order_item, make_test_sku

from app.core.domain import SKU, Batch
from app.entrypoints.flask_app import create_app
from app.repositories import UnitofWork, get_current_repo
from app.serializers import OrderItemSchema, SKUSchema


class TestAPI(ClientTestCase):
    app = create_app()

    # @unittest.skip
    def test_index(self, client: FlaskClient):
        rv = client.get("/")
        self.assertInResponse(b"Index", rv)

    # @unittest.skip
    def test_list_skus(self, client: FlaskClient):
        repo = get_current_repo()
        test_sku_1 = make_test_sku()
        test_sku_2 = make_test_sku()
        with UnitofWork(repo) as uow:
            uow.repo.add_all([test_sku_2, test_sku_1])

        response = client.get("/skus")

        data = json.loads(response.data)
        retrieved_skus = SKUSchema().load(response.json, many=True)
        # retrieved_skus = [SKU(**sku) for sku in data]

        self.assertTrue(test_sku_2 in retrieved_skus)
        self.assertTrue(test_sku_1 in retrieved_skus)

    def test_allocation_one_matching_batch_order_item_pair(self, client: FlaskClient):
        repo = get_current_repo()
        sku = make_test_sku()
        batch, order_item = make_test_batch_and_order_item(sku, 20, 2)
        with UnitofWork(repo) as uow:
            uow.repo.add(batch)

        response = client.post("/allocate", json=order_item.to_dict())
        # batch = repo.merge(batch)
        with UnitofWork(repo) as uow:
            batch = uow.repo.get(Batch, batch.uuid)
        # refreshed_batch = repo.get(Batch, batch.uuid)
        # data = response.data
        self.assertTrue(batch.available_quantity == 18)

        # self.assertTrue(data[0]["uuid"])
        # self.assertInResponse(b"", rv)
