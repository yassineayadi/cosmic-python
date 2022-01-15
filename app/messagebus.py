import logging
from typing import Callable, Dict, List, Type, Union

import services
from repositories import AbstractUnitOfWork

from app.core.commands import (
    AllocateCommand,
    ChangeBatchQuantity,
    Command,
    CreateProductCommand,
)
from app.core.events import Event, OutOfStock, ProductCreated

Message = Union[Event, Command]
logger = logging.getLogger(__name__)

QUEUE: List[Message] = []


def handle_event(event: Event):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            logger.debug("Handling Event %s with Handler %s", event, handler)
            handler(event)
        except Exception:
            logger.exception("Exception handling Event %s", event)
            raise


def handle_command(command: Command, queue: List[Message], uow: AbstractUnitOfWork):
    for handler in COMMAND_HANDLERS[type(command)]:
        try:
            logger.debug("Handling Command %s with Handler %s", command, handler)
            result = handler(command, uow)
            queue.extend(uow.collect_new_messages())
            return result
        except Exception:
            logger.exception("Exception handling Event %s", command)
            continue


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


# def register_handler(message_handlers: Dict, message: Type[Message], handler):
#     message_handlers[message].append(handler)
#
# def deregister_handler(message_handlers: Dict, message: Type[Message], handler):
#     message_handlers[message] = [hand for hand in message_handlers[message] if hand != handler]
#
# EVENT_HANDLER : Dict[Type[Event], List[Callable]] = defaultdict(list)
# COMMAND_HANDLERS: Dict[Type[Command], List[Callable]] = defaultdict(list)

EVENT_HANDLERS: Dict[Type[Event], List[Callable]] = {
    OutOfStock: [services.send_email_notification],
    ProductCreated: [services.mock_send_email_notification],
}

COMMAND_HANDLERS: Dict[Type[Command], List[Callable]] = {
    AllocateCommand: [services.allocate],
    CreateProductCommand: [services.create_product],
    ChangeBatchQuantity: [services.change_batch_quantity],
}
