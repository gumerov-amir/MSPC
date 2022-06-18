from __future__ import annotations
from enum import Enum, Flag
from logging import Logger
from typing import Any, Dict, List, TYPE_CHECKING
from urllib.parse import urlparse

from .. import mpv

import requests

import vk_api
from vk_api.exceptions import ApiError, ApiHttpError

from .service import SearchOptions, SearchType, Service
from .. import errors
from ..structs.artist import Artist
from ..structs.track import Track

if TYPE_CHECKING:
    from ..config import VkModel
    from ..translator import Translator


class VkService(Service):
    name = "vk"
    hostnames = [
        "vk.com",
        "www.vk.com",
        "vkontakte.ru",
        "www.vkontakte.ru",
        "m.vk.com",
        "m.vkontakte.ru",
    ]
    format = "mp3"

    def __init__(self, config: VkModel, logger: Logger, translator: Translator):
        self.config = config
        self.logger = logger
        self.translator = translator
        self.is_enabled = config.is_enabled

    def download(self, track: Track, file_path: str) -> None:
        if ".m3u8" not in track.url:
            super().download(track, file_path)
            return
        _mpv = mpv.MPV(
            **{
                "demuxer_lavf_o": "http_persistent=false",
                "ao": "null",
                "ao_null_untimed": True,
            }
        )
        _mpv.play(track.url)
        _mpv.record_file = file_path
        while not _mpv.idle_active:
            pass
        _mpv.terminate()

    def initialize(self) -> None:
        self.logger.debug("Initializing VK service")
        http = requests.Session()
        http.headers.update(
            {
                "User-agent": "VKAndroidApp/6.2-5091 (Android 9; SDK 28; samsungexynos7870; samsung j6lte; 720x1450)"
            }
        )
        self._session = vk_api.VkApi(
            token=self.config.token, session=http, api_version="5.131"
        )
        self.api = self._session.get_api()
        try:
            self.api.account.getInfo()
        except (
            ApiError,
            ApiHttpError,
            requests.exceptions.ConnectionError,
        ) as e:
            self.logger.error(e)
            raise errors.ServiceError(e)
        self.logger.debug("VK service has been initialized")

    def get_tracks(self, url: str, **kwargs: Any) -> List[Track]:
        parsed_url = urlparse(url)
        path = parsed_url.path[1::]
        if path.startswith("video_"):
            raise errors.ServiceError()
        audios: Dict[str, Any]
        try:
            if "music/" in path:
                id = path.split("/")[-1]
                ids = id.split("_")
                o_id = ids[0]
                p_id = ids[1]
                audios = self.api.audio.get(owner_id=int(o_id), album_id=int(p_id))
            elif "audio" in path:
                audios = {
                    "count": 1,
                    "items": self.api.audio.getById(audios=[path[5::]]),  # type: ignore
                }
            else:
                object_info = self.api.utils.resolveScreenName(screen_name=path)
                if object_info["type"] == "group":
                    id = -object_info["object_id"]
                else:
                    id = object_info["object_id"]
                audios = self.api.audio.get(owner_id=id, count=6000)
            if "count" in audios and audios["count"] > 0:
                tracks: List[Track] = []
                for audio in audios["items"]:
                    if "url" not in audio or not audio["url"]:
                        continue
                    track = Track(
                        title=audio["title"],
                        artists=[Artist(audio["artist"])],
                        url=audio["url"],
                        service=self,
                        format=self.format,
                    )
                    tracks.append(track)
                if tracks:
                    return tracks
                else:
                    raise errors.NothingFoundError()
            else:
                raise errors.NothingFoundError
        except NotImplementedError as e:
            self.logger.error(e)
            raise NotImplementedError()

    def search(
        self,
        query: str,
        search_type: Enum = SearchType.DEFAULT,
        search_options: Flag = SearchOptions.DEFAULT,
    ) -> List[Track]:
        results = self.api.audio.search(q=query, count=300, sort=0)
        if "count" in results and results["count"] > 0:
            tracks: List[Track] = []
            for track in results["items"]:
                if "url" not in track or not track["url"]:
                    continue
                track = Track(
                    title=track["title"],
                    artists=[Artist(track["artist"])],
                    url=track["url"],
                    service=self,
                    format=self.format,
                )
                tracks.append(track)
            if tracks:
                return tracks
            else:
                raise errors.NothingFoundError()
        else:
            raise errors.NothingFoundError()
