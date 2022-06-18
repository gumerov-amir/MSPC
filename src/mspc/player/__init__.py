from __future__ import annotations

import html
import random
import time
from logging import Logger
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING, Tuple

from .enums import Mode, State
from .sound_device import SoundDevice, SoundDeviceType
from .. import errors
from .. import mpv
from ..structs.artist import Artist
from ..structs.track import Track, TrackType

if TYPE_CHECKING:
    from ..config import PlayerModel
    from ..translator import Translator


class Player:
    mpv_options = {
        "demuxer_lavf_o": "http_persistent=false",
        "demuxer_max_back_bytes": 1048576,
        "demuxer_max_bytes": 2097152,
        "video": False,
        "ytdl": False,
    }

    def __init__(self, config: PlayerModel, logger: Logger, translator: Translator):
        self.config = config
        self.logger = logger
        self.mpv_options.update(self.config.player_options)
        try:
            self._player = mpv.MPV(**self.mpv_options, log_handler=self.log_handler)
        except AttributeError:
            del self.mpv_options["demuxer_max_back_bytes"]
            self._player = mpv.MPV(**self.mpv_options, log_handler=self.log_handler)
        self._log_level = 5
        self.track_list: List[Track] = []
        self.track: Track = Track()
        self.track_index: int = -1
        self._state = State.STOPPED
        self._mode = Mode.TRACK_LIST
        self._volume = self.config.default_volume

    def _parse_metadata(self, metadata: Dict[str, Any]) -> Tuple[Optional[str], ...]:
        stream_names = ["icy-name"]
        stream_name = None
        title = None
        artist = None
        for i in metadata:
            if i in stream_names:
                stream_name = html.unescape(metadata[i])
            if "title" in i:
                title = html.unescape(metadata[i])
            if "artist" in i:
                artist = html.unescape(metadata[i])
        return title, artist, stream_name

    def _play(self, arg: str) -> None:
        self._player.pause = False
        self._player.play(arg)

    def _shuffle(self, enable: bool) -> None:
        if enable:
            self._index_list = [i for i in range(0, len(self.track_list))]
            random.shuffle(self._index_list)
        else:
            del self._index_list

    def close(self) -> None:
        self.logger.debug("Closing player")
        if self._state != State.STOPPED:
            self.stop()
        self._player.terminate()
        self.logger.debug("Player closed")

    def get_duration(self) -> float:
        return self._player.duration

    def get_output_devices(self) -> List[SoundDevice]:
        devices: List[SoundDevice] = []
        for device in self._player.audio_device_list:
            devices.append(
                SoundDevice(
                    device["description"], device["name"], SoundDeviceType.OUTPUT
                )
            )
        return devices

    def get_position(self) -> float:
        return self._player.time_pos

    def get_speed(self) -> float:
        return self._player.speed

    def initialize(self) -> None:
        self.logger.debug("Initializing player")
        self.logger.debug("Player have been initialized")

    def log_handler(self, level: str, component: str, message: str) -> None:
        self.logger.log(self._log_level, "{}: {}: {}".format(level, component, message))

    @property
    def mode(self) -> Mode:
        return self._mode

    @mode.setter
    def mode(self, mode: Mode) -> None:
        if mode == Mode.RANDOM:
            self._shuffle(enable=True)
        else:
            try:
                self._shuffle(enable=False)
            except AttributeError:
                pass
        self._mode = mode

    def next(self) -> None:
        track_index = self.track_index
        if len(self.track_list) > 0:
            if self.mode == Mode.RANDOM:
                try:
                    track_index = self._index_list[
                        self._index_list.index(self.track_index) + 1
                    ]
                except IndexError:
                    track_index = 0
            else:
                track_index += 1
        else:
            track_index = 0
        try:
            self.play_by_index(track_index)
        except errors.IncorrectTrackIndexError:
            if self.mode == Mode.REPEAT_TRACK_LIST:
                self.play_by_index(0)
            else:
                raise errors.NoNextTrackError()

    def on_end_file(self, event: mpv.MpvEvent) -> None:
        if self._state == State.PLAYING and self._player.idle_active:
            if self.mode == Mode.SINGLE_TRACK or self.track.type == TrackType.DIRECT:
                self.stop()
            elif self.mode == Mode.REPEAT_TRACK:
                self.play_by_index(self.track_index)
            else:
                try:
                    self.next()
                except errors.NoNextTrackError:
                    self.stop()

    def on_metadata_update(self, name: str, value: Any) -> None:
        if self._state == State.PLAYING and (
            self.track.type == TrackType.DIRECT or self.track.type == TrackType.LOCAL
        ):
            metadata = self._player.metadata
            try:
                title, artist_name, stream_name = self._parse_metadata(metadata)
                if not title:
                    title = html.unescape(self._player.media_title)
            except TypeError:
                title = html.unescape(self._player.media_title)
                artist_name = None
                stream_name = None
            if title and self.track.title != title:
                self.track.title = title
            if artist_name is not None:
                self.track.artists = [Artist(artist_name)]
            if stream_name is not None:
                self.track.stream_name = stream_name

    def toggle_pause(self) -> None:
        if not self._player.pause:
            self._state = State.PAUSED
            self._player.pause = True
        else:
            self._state = State.PLAYING
            self._player.pause = False

    def play(
        self,
        tracks: Optional[List[Track]] = None,
        start_track_index: Optional[int] = None,
    ) -> None:
        if tracks is not None:
            self.track_list = tracks
            if not start_track_index and self.mode == Mode.RANDOM:
                self._shuffle(True)
                self.track_index = self._index_list[0]
                self.track = self.track_list[self.track_index]
            else:
                self.track_index = start_track_index if start_track_index else 0
                self.track = tracks[self.track_index]
            self._play(self.track.url)
        else:
            self._player.pause = False
        self._player.volume = self._volume
        self._state = State.PLAYING

    def play_by_index(self, index: int) -> None:
        if index < len(self.track_list) and index >= (0 - len(self.track_list)):
            self.track = self.track_list[index]
            self.track_index = self.track_list.index(self.track)
            self._play(self.track.url)
            self._state = State.PLAYING
        else:
            raise errors.IncorrectTrackIndexError()

    def previous(self) -> None:
        track_index = self.track_index
        if len(self.track_list) > 0:
            if self.mode == Mode.RANDOM:
                try:
                    track_index = self._index_list[
                        self._index_list.index(self.track_index) - 1
                    ]
                except IndexError:
                    track_index = len(self.track_list) - 1
            else:
                if track_index == 0 and self.mode != Mode.REPEAT_TRACK_LIST:
                    raise errors.NoPreviousTrackError
                else:
                    track_index -= 1
        else:
            track_index = 0
        try:
            self.play_by_index(track_index)
        except errors.IncorrectTrackIndexError:
            if self.mode == Mode.REPEAT_TRACK_LIST:
                self.play_by_index(len(self.track_list) - 1)
            else:
                raise errors.NoPreviousTrackError

    @property
    def state(self) -> State:
        return self._state

    def stop(self) -> None:
        self._state = State.STOPPED
        self._player.stop()
        self.track_list = []
        self.track = Track()
        self.track_index = -1

    def seek_back(self, step: Optional[float] = None) -> None:
        step = step if step else self.config.seek_step
        if step <= 0:
            raise ValueError()
        try:
            self._player.seek(-step, reference="relative")
        except SystemError:
            self.stop()

    def seek_forward(self, step: Optional[float] = None) -> None:
        step = step if step else self.config.seek_step
        if step <= 0:
            raise ValueError()
        try:
            self._player.seek(step, reference="relative")
        except SystemError:
            self.stop()

    def set_output_device(self, sound_device: SoundDevice) -> None:
        self._player.audio_device = sound_device.id

    def set_position(self, arg: float) -> None:
        if arg < 0:
            raise errors.IncorrectPositionError()
        self._player.seek(arg, reference="absolute")

    def set_speed(self, arg: float) -> None:
        if arg < 0.25 or arg > 4:
            raise ValueError()
        self._player.speed = arg

    def set_volume(self, volume: int) -> None:
        volume = volume if volume <= self.config.max_volume else self.config.max_volume
        self._volume = volume
        if self.config.volume_fading:
            n = 1 if self._player.volume < volume else -1
            for i in range(int(self._player.volume), volume, n):
                self._player.volume = i
                time.sleep(self.config.volume_fading_interval)
        else:
            self._player.volume = volume

    def register_event_callback(
        self, callback_name: str, callback_func: Callable[[mpv.MpvEvent], None]
    ) -> None:
        self._player.event_callback(callback_name)(callback_func)

    def run(self) -> None:
        self.logger.debug("Registering player callbacks")
        self.register_event_callback("end-file", self.on_end_file)
        self._player.observe_property("metadata", self.on_metadata_update)
        self._player.observe_property("media-title", self.on_metadata_update)
        self.logger.debug("Player callbacks registered")
