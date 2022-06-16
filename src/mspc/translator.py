import gettext

from .config import TranslatorModel


class Translator:
    def __init__(self, config: TranslatorModel):
        self.locale_domain = config.locale_domain
        self.locale_dir = config.locale_dir
        self.locale = config.locale

    @property
    def locale(self) -> str:
        return self._locale

    @locale.setter
    def locale(self, locale: str) -> None:
        self._locale = locale
        self.translation = gettext.translation(
            self.locale_domain,
            self.locale_dir,
            languages=[locale],
            fallback=True,
        )

    def translate(self, message: str) -> str:
        return self.translation.gettext(message)
