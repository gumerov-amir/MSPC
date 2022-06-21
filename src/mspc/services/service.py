from __future__ import annotations
from abc import ABCMeta, abstractmethod
from enum import Enum, Flag
from typing import Any, List, TYPE_CHECKING

from .. import downloader

if TYPE_CHECKING:
    from ..structs.playlist import Playlist
    from ..structs.track import Track


class SearchType(Enum):
    DEFAULT = 0


class SearchOptions(Flag):
    DEFAULT = 0


class Service(metaclass=ABCMeta):
    name: str
    is_enabled: bool
    is_extended: bool = False
    is_hidden: bool = False
    hostnames: List[str] = []
    ext: Exception

    def close(self) -> None:
        pass

    def download(self, track: Track, file_path: str) -> None:
        downloader.download_file(track.url, file_path)

    def get_my_playlists(self) -> List[Playlist]:
        raise NotImplementedError

    @abstractmethod
    def get_tracks(
        self,
        url: str,
        **kwargs: Any,
    ) -> List[Track]:
        ...

    @abstractmethod
    def initialize(self) -> None:
        ...

    def prepare_track(self, track: Track) -> Track:
        ...

    def search(
        self,
        query: str,
        search_type: Enum = SearchType.DEFAULT,
        search_options: Flag = SearchOptions.DEFAULT,
    ) -> List[Track]:
        ...

    def run(self) -> None:
        pass
