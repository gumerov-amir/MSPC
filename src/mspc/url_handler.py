from __future__ import annotations

from typing import List, TYPE_CHECKING
from urllib.parse import urlparse

from . import errors
from .structs.track import Track, TrackType

if TYPE_CHECKING:
    from .services import ServiceManager


class UrlHandler:
    def __init__(self, service_manager: ServiceManager):
        self.allowed_schemes: List[str] = ["http", "https", "rtmp", "rtsp"]
        self.service_manager = service_manager

    def get_tracks(self, url: str) -> List[Track]:
        parsed_url = urlparse(url)
        if parsed_url.scheme in self.allowed_schemes:
            track = Track(url=url, type=TrackType.DIRECT)
            fetched_data = [track]
            for service in self.service_manager.services.values():
                try:
                    if (
                        parsed_url.hostname in service.hostnames
                        or service.name == self.service_manager.fallback_service
                    ):
                        fetched_data = service.get_tracks(url)
                        break
                except errors.ServiceError:
                    continue
                except Exception:
                    if service.name == self.service_manager.fallback_service:
                        return [
                            track,
                        ]
            if len(fetched_data) == 1 and fetched_data[0].url.startswith(track.url):
                return [
                    track,
                ]
            else:
                return fetched_data
        else:
            raise errors.IncorrectProtocolError
