from __future__ import annotations
from enum import Enum, Flag, auto
from logging import Logger
from typing import Any, List, TYPE_CHECKING
from urllib.parse import urlparse

from yandex_music import Client
from yandex_music.exceptions import UnauthorizedError
from yandex_music.track.track import Track as YamTrack

from .service import Service
from .. import errors
from ..structs.artist import Artist
from ..structs.track import Track, TrackType

if TYPE_CHECKING:
    from ..config import YamModel
    from ..translator import Translator


class YamSearchType(Enum):
    DEFAULT = auto()
    ALL = DEFAULT
    TRACK = auto()
    PODCAST_EPISODE = auto()


class YamSearchOptions(Flag):
    DEFAULT = 0
    NOCORRECT = auto()


class YamService(Service):
    name = "yandex-music"
    hostnames = ["music.yandex.ru"]
    format = ".mp3"

    def __init__(self, config: YamModel, logger: Logger, translator: Translator):
        self.config = config
        self.logger = logger
        self.translator = translator
        self.is_enabled = self.config.is_enabled

    def initialize(self) -> None:
        self.logger.debug("Initializing Yandex-music service")
        self.api = Client(token=self.config.token)  # type: ignore
        try:
            self.api.init()
        except UnauthorizedError as e:
            raise errors.ServiceError(e)
        acc_status = self.api.account_status()
        if acc_status is None or not acc_status.account.uid:
            self.warning_message = self.translator.translate("Token is not provided")
        elif acc_status.plus is None or not acc_status.plus.has_plus:
            self.warning_message = self.translator.translate(
                "You don't have Yandex Plus"
            )
        self.logger.debug("Yandex-music service has been initialized")

    def get_tracks(self, url: str, **kwargs: Any) -> List[Track]:
        parsed_data = urlparse(url)
        path = parsed_data.path
        yam_tracks: List[YamTrack] = []
        if "/album/" in path and "/track/" in path:
            split_path = path.split("/")
            real_id = split_path[4] + ":" + split_path[2]
            yam_tracks.append(self.api.tracks(real_id)[0])
        elif "/album/" in path:
            album = self.api.albums_with_tracks(path.split("/")[2])
            if album is None or album.volumes is None or len(album.volumes[0]) == 0:
                raise errors.ServiceError()
            for volume in album.volumes:
                for track in volume:
                    yam_tracks.append(track)
        if "/artist/" in path:
            artist_tracks = self.api.artists_tracks(path.split("/")[2])
            if artist_tracks is None:
                raise errors.ServiceError()
            for track in artist_tracks.tracks:
                yam_tracks.append(track)
        elif "users" in path and "playlist" in path:
            split_path = path.split("/")
            user_id = split_path[2]
            kind = split_path[4]
            playlist = self.api.users_playlists(kind=kind, user_id=user_id)
            if playlist is None:
                raise errors.ServiceError()
            elif isinstance(playlist, list):
                playlist = playlist[0]  # it is temperary solution
            for track_short in playlist.tracks:
                track = track_short.fetch_track()
                yam_tracks.append(track)
        else:
            raise errors.ServiceError(
                self.translator.translate("This link is not supported")
            )
        tracks: List[Track] = []
        for yam_track in yam_tracks:
            tracks.append(
                Track(
                    title=str(yam_track.title),
                    artists=[
                        Artist(str(artist.name), str(artist.id), self)
                        for artist in yam_track.artists
                    ]
                    if yam_track.artists
                    else [],
                    extra_info={"track_id": yam_track.track_id},
                    service=self,
                    type=TrackType.Dynamic,
                )
            )
        return tracks

    def prepare_track(self, track: Track) -> Track:
        yam_tracks = self.api.tracks(track.extra_info["track_id"])
        if yam_tracks is None:
            raise errors.ServiceError()
        yam_track = yam_tracks[0]
        return Track(
            title=track.title,
            artists=track.artists,
            url=str(yam_track.get_download_info(get_direct_links=True)[0].direct_link),
            format=self.format,
        )

    def search(
        self,
        query: str,
        search_type: Enum = YamSearchType.DEFAULT,
        search_options: Flag = YamSearchOptions.DEFAULT,
    ) -> List[Track]:
        nocorrect = (
            True
            if search_options & YamSearchOptions.NOCORRECT == YamSearchOptions.NOCORRECT
            else False
        )
        if search_type == YamSearchType.ALL:
            found_tracks = self.api.search(text=query, nocorrect=nocorrect, type_="all")
            if found_tracks is None:
                raise errors.ServiceError
            if found_tracks.tracks is None:
                raise errors.NothingFoundError
            yam_tracks = found_tracks.tracks.results
        elif search_type == YamSearchType.TRACK:
            found_tracks = self.api.search(
                text=query, nocorrect=nocorrect, type_="tracks"
            )
            if found_tracks is None:
                raise errors.ServiceError
            if found_tracks.tracks is None:
                raise errors.NothingFoundError
            yam_tracks = found_tracks.tracks.results
        elif search_type == YamSearchType.PODCAST_EPISODE:
            found_podcast_episodes = self.api.search(
                text=query, nocorrect=nocorrect, type_="podcast_episode"
            )
            if found_podcast_episodes is None:
                raise errors.ServiceError
            if found_podcast_episodes.podcast_episodes is None:
                raise errors.NothingFoundError
            yam_tracks = found_podcast_episodes.podcast_episodes.results
        else:
            raise NotImplementedError
        tracks: List[Track] = []
        yam_track: YamTrack
        for yam_track in yam_tracks:
            tracks.append(
                Track(
                    title=str(yam_track.title),
                    artists=[
                        Artist(str(artist.name), artist.id, self)
                        for artist in yam_track.artists
                    ] if yam_track.artists else [],
                    extra_info={"track_id": yam_track.track_id},
                    service=self,
                    type=TrackType.Dynamic,
                )
            )
        if tracks:
            return tracks
        else:
            raise errors.NothingFoundError("")
