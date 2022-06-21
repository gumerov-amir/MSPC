from __future__ import annotations
from enum import Enum, Flag
from logging import Logger
from typing import Any, List, TYPE_CHECKING

from youtubesearchpython import VideosSearch

from yt_dlp import YoutubeDL

from .service import SearchOptions, SearchType, Service
from .. import errors
from ..structs.artist import Artist
from ..structs.track import Track, TrackType

if TYPE_CHECKING:
    from ..config import YtModel


class YtService(Service):
    name = "yt"

    def __init__(self, config: YtModel, logger: Logger):
        self.config = config
        self.logger = logger
        self.is_enabled = self.config.is_enabled

    def initialize(self) -> None:
        self.logger.debug("Initializing YT service")
        self._ydl_config = {
            "skip_download": True,
            "format": "m4a/bestaudio/best",
            "socket_timeout": 5,
            "logger": self.logger,
        }
        self.logger.debug("YT service has been initialized")

    def get_tracks(self, url: str, **kwargs: Any) -> List[Track]:
        extra_info = kwargs["extra_info"] if "extra_info" in kwargs else None
        with YoutubeDL(self._ydl_config) as ydl:
            if not extra_info:
                info = ydl.extract_info(url, process=False)
            else:
                info = extra_info
            info_type = None
            if "_type" in info:
                info_type = info["_type"]
            if info_type == "url" and not info["ie_key"]:
                return self.get_tracks(info["url"])
            elif info_type == "playlist":
                tracks: List[Track] = []
                for entry in info["entries"]:
                    data = self.get_tracks("", extra_info=entry)
                    tracks += data
                return tracks
            return [
                Track(
                    title=info["title"],
                    extra_info=info,
                    service=self,
                    type=TrackType.Dynamic,
                )
            ]

    def prepare_track(self, track: Track) -> Track:
        with YoutubeDL(self._ydl_config) as ydl:
            info = track.extra_info
            if info is None:
                raise errors.ServiceError
            try:
                stream = ydl.process_ie_result(info)
            except Exception:
                raise errors.ServiceError()
            if "url" in stream:
                url = str(stream["url"])
            else:
                raise errors.ServiceError()
            title = str(stream["title"])
            if "uploader" in stream:
                artists = [Artist(str(stream["uploader"]["name"]))]
            else:
                artists = []
            format = str(stream["ext"])
            if "is_live" in stream and stream["is_live"]:
                type = TrackType.Live
            else:
                type = TrackType.Default
            return Track(
                title=title, artists=artists, url=url, format=format, type=type
            )

    def search(
        self,
        query: str,
        search_type: Enum = SearchType.DEFAULT,
        search_options: Flag = SearchOptions.DEFAULT,
    ) -> List[Track]:
        search = VideosSearch(query, limit=300).result()
        if search["result"]:
            tracks: List[Track] = []
            for video in search["result"]:
                track = Track(title=video["title"], artists=[Artist(video["channel"])], url=video["link"], service=self, type=TrackType.Dynamic)
                tracks.append(track)
            return tracks
        else:
            raise errors.NothingFoundError("")
