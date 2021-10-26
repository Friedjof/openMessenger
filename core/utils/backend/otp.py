# Friedjof Noweck
# 19.08.2021 Do

import pyotp

from core.utils.backend.configuration import Configuration


class TotpType:
     class User:
         Description: str = None

     class Token:
         Description: str = None


class Totp:
    def __init__(self, configuration: Configuration, userID: str, totpKey: str = None,
                 totpType: TotpType.Token or TotpType.User = TotpType.User):
        self.userID = userID
        self.config: Configuration = configuration
        self.totpType = totpType

        if totpKey is None:
            self.totpKey: str = self._gen_key()
        else:
            self.totpKey: str = totpKey

    def now(self) -> str:
        return pyotp.TOTP(self.totpKey).now()

    def verify(self, code: str):
        return pyotp.TOTP(self.totpKey).verify(code)

    def _gen_key(self) -> str:
        return pyotp.random_base32()

    def _gen_url(self) -> str:
        return pyotp.TOTP(self.totpKey).provisioning_uri(
            name=self.userID,
            issuer_name=self.config.conf.application["name"]
        )


# tokenTOTP Example
if __name__ == "__main__":
    config = Configuration(path="../../../server/backend/config/Configuration.yaml", configPaths=False).load()
    totp = Totp(
        configuration=config,
        userID=config.uuid.generate(),
    )

    print(totp.totpKey)
    print(totp.verify(totp.now()))
