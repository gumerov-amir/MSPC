from __future__ import annotations
import sys
from logging import Logger
from typing import Dict, List, TYPE_CHECKING

from .vk import VkService
from .yam import YamService
from .yt import YtService
from .. import errors, vars
from ..config import ServicesModel

if TYPE_CHECKING:
    from .service import Service


class ServiceManager:
    def __init__(self, config: ServicesModel, logger: Logger) -> None:
        self.config = config
        self.logger = logger
        self.fallback_service = vars.fallback_service
        self.services: Dict[str, Service]
        self.services = {
            "vk": VkService(self.config.vk, self.logger),
            "yam": YamService(self.config.yam, self.logger),
            "yt": YtService(self.config.yt, self.logger),
        }
        self.service: Service = self.services[self.config.default_service]
        self.failed_services: List[Service] = []

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
            except errors.ServiceError:
                self.failed_services.append(service)
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
