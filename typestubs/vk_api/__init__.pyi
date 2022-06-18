from typing import Any, Dict

import requests



class Audio:
    def get(
        self,
        owner_id: int = ...,
        album_id: int = ...,
        count: int = ...,
    ) -> Dict[str, Any]: ...

    def search(
        self, q: str = ..., count: int = ..., sort: int = ...
    ) -> Dict[str, Any]: ...


class Account:
    def getInfo(self) -> Dict[str, Any]: ...


class Utils:
    def resolveScreenName(self, screen_name: str = ...) -> Dict[str, Any]: ...


class Api:
    account: Account
    audio: Audio
    utils: Utils


class VkApi:
    def __init__(
        self,
        token: str = ...,
        session: requests.Session = ...,
        api_version: str = ...,
    ) -> None: ...

    def get_api(self) -> Api: ...
