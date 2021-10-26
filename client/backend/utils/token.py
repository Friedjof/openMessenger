# Friedjof Noweck
# 20.08.2021 Fr
import pyotp

from client.backend.utils.cacheManagement import CacheManager
from core.utils.backend.configuration import Configuration
from core.utils.backend.otp import Totp, TotpType


class Token:
    def __init__(self, configuration: Configuration, payload: dict = None,
                 tokenId: str = None, tokenTOTP: Totp = None):
        self._config = configuration
        self.payload: dict = payload

        self._config.log.log(self._config.logStatus.DEBUG, msg=f"> Token payload: {self.payload}", ignore=True)

        self.cacheManager = CacheManager(configuration=self._config)

        if self.payload is not None:
            self.set_payload(self.payload)
        else:
            self.tokenId: str = tokenId
            self.tokenTOTP: Totp = tokenTOTP

    def set_payload(self, payload: dict):
        self.payload: dict = payload
        self.tokenId: str = self.payload["tokenId"]
        self._config.log.log(self._config.logStatus.DEBUG, msg=f"tokenTOTP: {self.payload['tokenTOTP']}", ignore=True)
        self.tokenTOTP: Totp = Totp(
            configuration=self._config,
            userID=self.tokenId,
            totpType=TotpType.Token,
            totpKey=self.payload["tokenTOTP"]
        )

    def as_dict(self) -> dict:
        return {"tokenId": self.tokenId, "tokenTOTP": self.tokenTOTP.totpKey}

    def as_login_dict(self) -> dict:
        self.load()
        return {"tokenId": self.tokenId, "tokenTOTP": pyotp.TOTP(self.tokenTOTP.totpKey).now()}

    def now(self) -> str:
        return self.tokenTOTP.now()

    def reset_token_cache(self):
        cache: dict = self.cacheManager.read()
        cache["token"] = {"tokenId": None, "tokenTOTP": None}
        self.cacheManager.write(cache=cache)

    def clear(self):
        self.reset_token_cache()

    def is_cached(self) -> bool:
        try:
            cache: dict = self.cacheManager.read()
            self._config.log.log(self._config.logStatus.DEBUG, msg=f">>> Token: {cache['token']}", ignore=True)
            return cache['token']["tokenId"] is not None or cache['token']["tokenId"] is not None
        except KeyError:
            self.reset_token_cache()
            self._config.log.log(self._config.logStatus.WARNING, f"Cache not available.")
            return False

    def set(self, payload: dict = None, tokenId: str = None, tokenTOTP: str = None):
        if payload is not None:
            self.tokenId: str = tokenId
            self.tokenTOTP: Totp = Totp(
                configuration=self._config,
                userID=self.tokenId,
                totpType=TotpType.Token,
                totpKey=tokenTOTP
            )

        return self

    def load(self):
        try:
            token: dict = self.cacheManager.read()["token"]
            self.tokenId = token["tokenId"]
            self.tokenTOTP: Totp = Totp(
                configuration=self._config,
                userID=self.tokenId,
                totpType=TotpType.Token,
                totpKey=token["tokenTOTP"]
            )
        except KeyError:
            self.reset_token_cache()

    def save(self) -> None:
        try:
            cache = self.cacheManager.read()
            cache["token"] = self.as_dict()
            self.cacheManager.write(cache)
            self._config.log.log(self._config.logStatus.DEBUG, f"Cache: {cache}", ignore=True)
            self._config.log.log(self._config.logStatus.SUCCESSFUL, f"Token successfully saved.", ignore=True)
        except KeyError:
            self.reset_token_cache()
            self._config.log.log(self._config.logStatus.WARNING, f"Token could not be saved.")
