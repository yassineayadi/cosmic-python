import unittest

from app.config import get_current_config
from app.core.domain import Batch, OrderItem
from app.repositories import ABCRepo, UnitofWork, get_current_repo
from tests.test_domain import (
    make_test_batch_and_order_item,
    make_test_order_item,
    make_test_sku,
)


class TestUnitOfWork(unittest.TestCase):
    def test_create_uow(self):
        uow = UnitofWork(get_current_repo())
        self.assertIsInstance(uow, UnitofWork)

    def test_successful_open_repo_on_enter(self):
        uow = UnitofWork(get_current_repo())

        with uow as uow:
            self.assertTrue(uow.repo.session is not None)

    def test_successful_close_repo_on_exit(self):
        uow = UnitofWork(get_current_repo())
        with uow as uow:
            pass


class TestRepository(unittest.TestCase):
    repo: ABCRepo

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = get_current_repo()
        cls.repo.open_session()

    @classmethod
    def tearDownClass(cls):
        cls.repo.close()

    @unittest.skip(reason="Instantiated in setUpClass method.")
    def test_setup_repo(self):
        repo = get_current_repo()
        print(repo)

    def test_save_order_item(self):
        # order_item = make_test_order_item()
        batch_1, order_item_1 = make_test_batch_and_order_item(make_test_sku(), 20, 10)
        with UnitofWork(self.repo) as uow:
            batch_1.allocate_available_quantity(order_item_1)
            uow.repo.add(order_item_1)

        print(order_item_1)

    def test_delete_order_item(self):
        order_item = make_test_order_item()
        self.repo.add(order_item)
        order_item_copy = self.repo.get(OrderItem, order_item.uuid)
        self.repo
        self.assertEqual(order_item.uuid, order_item_copy.uuid)

    def test_insert_order_item_multiple_times(self):
        order_item = make_test_order_item()
        self.repo.add(order_item)
        self.repo.add(order_item)
        retrieved_order_item = self.repo.get(OrderItem, order_item.uuid)
        self.assertTrue(order_item is retrieved_order_item)

    def test_insert_batch(self):
        sku = make_test_sku()
        batch, _ = make_test_batch_and_order_item(sku, 20, 2)
        self.repo.add(batch)
        retrieved_batch = self.repo.get(Batch, batch.uuid)
        self.assertTrue(retrieved_batch == batch)

    def test_create_allocate_and_retrieve_same_batches(self):
        sku = make_test_sku()
        batch, order_item = make_test_batch_and_order_item(sku, 20, 2)
        batch.allocate_available_quantity(order_item)
        self.repo.add(batch)
        retrieved_batch = self.repo.get(Batch, batch.uuid)
        self.assertTrue(retrieved_batch == batch)
