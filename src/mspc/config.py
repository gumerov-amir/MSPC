from typing import Any, Dict

from pydantic import BaseModel


class PlayerModel(BaseModel):
    language: str = "en"
    default_volume: int = 50
    max_volume: int = 100
    volume_fading: bool = True
    volume_fading_interval: float = 0.025
    seek_step: int = 5
    player_options: Dict[str, Any] = {}


class VkModel(BaseModel):
    is_enabled: bool = True
    token: str = ""


class YtModel(BaseModel):
    is_enabled: bool = True


class YamModel(BaseModel):
    is_enabled: bool = True
    token: str = ""


class ServicesModel(BaseModel):
    default_service: str = "vk"
    vk: VkModel = VkModel()
    yam: YamModel = YamModel()
    yt: YtModel = YtModel()


class TranslatorModel(BaseModel):
    locale: str = "en"
    locale_domain: str = "MSPC"
    locale_dir: str = "locale"


class ConfigModel(BaseModel):
    language: str = "en"
    player: PlayerModel = PlayerModel()
    services: ServicesModel = ServicesModel()
    translator: TranslatorModel = TranslatorModel()


def get_default_config_dict() -> Dict[str, Any]:
    return ConfigModel().dict()
