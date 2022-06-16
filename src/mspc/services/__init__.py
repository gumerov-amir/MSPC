from __future__ import annotations
import sys
from logging import Logger
from typing import Dict, TYPE_CHECKING

from .vk import VkService
from .yam import YamService
from .yt import YtService
from .. import errors, vars
from ..config import ServicesModel

if TYPE_CHECKING:
    from .service import Service
    from ..translator import Translator


class ServiceManager:
    def __init__(
        self, config: ServicesModel, logger: Logger, translator: Translator
    ) -> None:
        self.config = config
        self.logger = logger
        self.translator = translator
        self.fallback_service = vars.fallback_service
        self.services: Dict[str, Service]
        self.services = {
            "vk": VkService(self.config.vk, self.logger, self.translator),
            "yam": YamService(self.config.yam, self.logger, self.translator),
            "yt": YtService(self.config.yt, self.logger, self.translator),
        }
        self.service: Service = self.services[self.config.default_service]

    def close(self) -> None:
        self.logger.debug("Closing services")
        for service in self.services.values():
            service.close()
        self.logger.debug("Services have been closed")

    def initialize(self) -> None:
        self.logger.debug("Initializing services")
        for service in self.services.values():
            if not service.is_enabled:
                continue
            try:
                service.initialize()
            except errors.ServiceError as e:
                service.is_enabled = False
                service.error_message = str(e)
                if service == self.service:
                    self.service = self.services[self.fallback_service]
        self.logger.debug("Services have been initialized")

    def run(self) -> None:
        self.logger.debug("Running services")
        for service in self.services.values():
            if service.is_enabled:
                try:
                    service.run()
                except errors.ServiceError as e:
                    sys.exit(str(e))
        self.logger.debug("Services have been started")
