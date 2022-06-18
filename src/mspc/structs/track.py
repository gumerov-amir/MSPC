from __future__ import annotations
import os
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .. import utils

if TYPE_CHECKING:
    from .artist import Artist
    from ..services import Service


class TrackType(Enum):
    Default = 0
    Live = 1
    LOCAL = 2
    DIRECT = 3
    Dynamic = 4


class Track:
    format: str
    stream_name: str
    type: TrackType

    def __init__(
        self,
        title: str = "",
        artists: List[Artist] = [],
        url: str = "",
        service: Optional[Service] = None,
        extra_info: Dict[str, Any] = {},
        format: str = "",
        type: TrackType = TrackType.Default,
    ) -> None:
        self.title = title
        self.artists = artists
        self.url = url
        self.service = service
        self.extra_info = extra_info
        self.format = format
        self.type = type
        self._is_fetched = False

    def download(self, directory: str) -> str:
        if not self.service:
            raise NotImplementedError
        artists = "&".join([artist.name for artist in self.artists])
        file_name = f"{artists} - {self.title}" + "." + self.format
        file_name = utils.clean_file_name(file_name)
        file_path = os.path.join(directory, file_name)
        self.service.download(self, file_path)
        return file_path

    def _fetch_stream_data(self):
        if self.type != TrackType.Dynamic or self._is_fetched or not self.service:
            return
        if self.extra_info:
            prepared_track = self.service.prepare_track(self)
        else:
            prepared_track = self.service.get_tracks(self._url)[0]
        self.url = prepared_track.url
        self._is_fetched = True

    @property
    def url(self) -> str:
        self._fetch_stream_data()
        return self._url

    @url.setter
    def url(self, value: str) -> None:
        self._url = value

    def __bool__(self):
        if self.service or self.url:
            return True
        else:
            return False
