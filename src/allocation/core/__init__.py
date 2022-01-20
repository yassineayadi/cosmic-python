from typing import Union

from .commands import Command
from .events import Event

Message = Union[Event, Command]
