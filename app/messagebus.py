import smtplib
from typing import Callable, Dict, List, Type

from app.core.events import Event, OutOfStockEvent


def send_out_email_notification(event: OutOfStockEvent):
    server = smtplib.SMTP('localhost')
    server.sendmail(f"You are being notified that the following SKU {OutOfStockEvent.sku_id} is OutOfStock")
    server.quit()


def handle(event: Event):
    for handler in HANDLERS[type(event)]:
        handler(event)


HANDLERS: Dict[Type[Event], List[Callable]] = {
    OutOfStockEvent: [send_out_email_notification]
}