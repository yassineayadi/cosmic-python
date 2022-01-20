import logging
from typing import Callable, Dict, List, Type

from allocation import services
from allocation.core import Message
from allocation.core.commands import (
    Allocate,
    ChangeBatchQuantity,
    Command,
    CreateProductCommand,
)
from allocation.core.events import (
    Event,
    OrderItemAllocated,
    OrderItemDeallocated,
    OutOfStock,
    ProductCreated,
)
from allocation.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)

QUEUE: List[Message] = []


def handle_event(event: Event):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            logger.debug("Handling Event %s with Handler %s", event, handler)
            handler(event)
        except Exception:
            logger.exception("Exception handling Event %s", event)
            continue


def handle_command(command: Command, queue: List[Message], uow: AbstractUnitOfWork):
    for handler in COMMAND_HANDLERS[type(command)]:
        try:
            logger.debug("Handling Command %s with Handler %s", command, handler)
            result = handler(command, uow)
            queue.extend(uow.collect_new_messages())
            return result
        except Exception:
            logger.exception("Exception handling Event %s", command)
            raise


def handle(queue: List[Message], uow: AbstractUnitOfWork):
    results = []
    while queue:
        message = queue.pop(0)
        if isinstance(message, Event):
            handle_event(message)
        elif isinstance(message, Command):
            cmd_results = handle_command(message, queue, uow)
            results.append(cmd_results)
        else:
            raise Exception(f"Message {message} was not an Event or Command.")


EVENT_HANDLERS: Dict[Type[Event], List[Callable]] = {
    OutOfStock: [services.send_email_notification],
    ProductCreated: [services.mock_send_email_notification],
    OrderItemAllocated: [services.publish_message_to_external_bus],
    OrderItemDeallocated: [
        services.publish_message_to_external_bus,
        services.mock_send_email_notification,
    ],
}

COMMAND_HANDLERS: Dict[Type[Command], List[Callable]] = {
    Allocate: [services.allocate],
    CreateProductCommand: [services.create_product],
    ChangeBatchQuantity: [services.change_batch_quantity],
}
