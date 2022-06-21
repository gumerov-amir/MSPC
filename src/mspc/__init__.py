from logging import Logger, root
from typing import Any, Dict, List


from .config import ConfigModel
from .player import Player
from .services import ServiceManager
from .services.service import Service
from .structs.track import Track
from .url_handler import UrlHandler


class MSPC:
    def __init__(self, config: Dict[str, Any] = {}, logger: Logger = root):
        self.config = ConfigModel(**config)
        self.logger = logger
        self.player = Player(self.config.player, self.logger)
        self.service_manager = ServiceManager(
            self.config.services, self.logger
        )
        self.url_handler = UrlHandler(self.service_manager)

    def __delete__(self) -> None:
        self.close()

    def close(self) -> None:
        self.logger.info("Closing MSPC")
        self.player.close()
        self.service_manager.close()
        self.logger.info("MSPC was closed")

    def get_services(self) -> Dict[str, Service]:
        services: Dict[str, Service] = {}
        for service in self.service_manager.services.values():
            if not service.is_hidden:
                services[service.name] = service
        return services

    def get_tracks_from_url(self, url: str) -> List[Track]:
        return self.url_handler.get_tracks(url)

    def initialize(self) -> None:
        self.logger.info("Initializing MSPC")
        self.player.initialize()
        self.service_manager.initialize()
        self.logger.info("MSPC was initialized")

    def run(self) -> None:
        self.logger.info("Running MSPC")
        self.player.run()
        self.service_manager.run()
        self.logger.info("MSPC was started")
