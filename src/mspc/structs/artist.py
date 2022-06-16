from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Union

if TYPE_CHECKING:
    from ..services import Service


class Artist:
    def __init__(
        self,
        name: str,
        id: Optional[Union[str, int]] = None,
        service: Optional[Service] = None,
    ):
        self.name = name
        self.id = id
        self.service = service
