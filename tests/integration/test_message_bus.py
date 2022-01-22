from conftest import make_test_sku

from allocation import messagebus
from allocation.core import Message, commands, events
from allocation.messagebus import EVENT_HANDLERS
from allocation.repositories import MockRepo
from allocation.unit_of_work import MockUnitOfWork


def mock_send_email_notification(msg: Message):
    print("Sending Event notification to mock@staff.com...")
    print(msg)
    print("Notification sent!")


EVENT_HANDLERS[events.ProductCreated] = [mock_send_email_notification]


def test_handle_event():
    sku = make_test_sku()
    msg = events.ProductCreated(sku.uuid)
    messagebus.handle_event(msg)


def test_insert_message_into_queue():
    sku = make_test_sku()
    msg = events.ProductCreated(sku.uuid)
    messagebus.QUEUE.append(msg)
    uow = MockUnitOfWork(MockRepo())
    assert len(messagebus.QUEUE) == 1
    messagebus.handle(messagebus.QUEUE, uow)
    assert len(messagebus.QUEUE) == 0


def test_handle_workflow_from_command_to_event():
    sku = make_test_sku()
    cmd = commands.CreateProductCommand(sku)
    uow = MockUnitOfWork(MockRepo())
    messagebus.handle([cmd], uow)
    with uow:
        product = uow.products.list().pop()
        assert product.sku.name == sku.name


def test_generate_event_after_command_handled():
    sku = make_test_sku()
    cmd = commands.CreateProductCommand(sku)
    uow = MockUnitOfWork(MockRepo())
    messagebus.handle_command(cmd, messagebus.QUEUE, uow)
    assert isinstance(messagebus.QUEUE.pop(), events.ProductCreated)
