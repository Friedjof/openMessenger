# Friedjof Noweck
# 18.08.2021 Mi
import base64
import bcrypt
import hashlib
import random
import string
import re
from difflib import SequenceMatcher

from core.utils.backend.configuration import Configuration


class PasswordReviewMessages:
    class ErrorTypes:
        class PasswordTooShort(Exception):
            IsPositive: bool = False
            Message: str = "This password is too Short."

        class PasswordTooLong(Exception):
            IsPositive: bool = False
            Message: str = "This password is too Long."

        class PasswordMustHave(Exception):
            IsPositive: bool = False
            Message: str = "This password does not contain all security features."

        class PasswordMustNot(Exception):
            IsPositive: bool = False
            Message: str = "This password contains characters that are not allowed."

    class SuccessfulTypes:
        class Successful:
            IsPositive: bool = True
            Message: str = "This password is secure."


class PasswordType:
    UserPassword: int = 0
    SessionPassword: int = 1
    Null: int = None


class Password:
    def __init__(self, configuration: Configuration, password: str = None, description: str = None, passwordType: PasswordType or int = PasswordType.Null):
        self.description = description
        self.passwordType = passwordType

        self._config = configuration

        self.password = password
        self.salt = bcrypt.gensalt(12)
        self.pool = None
        self.length = None

        if password is not None:
            self._hash = self._gen_hash()
        else:
            self._hash = None

    def _validation_is(self, password: str) -> PasswordReviewMessages.ErrorTypes or PasswordReviewMessages.SuccessfulTypes:
        if len(password) < self._config.conf.password["is_secure"]["length"]["min"]:
            return PasswordReviewMessages.ErrorTypes.PasswordTooShort
        if len(password) >= self._config.conf.password["is_secure"]["length"]["max"]:
            return PasswordReviewMessages.ErrorTypes.PasswordTooLong

        for must_have in self._config.conf.password["is_secure"]["must_have"]:
            if not re.search(must_have, password):
                return PasswordReviewMessages.ErrorTypes.PasswordMustHave

        for must_not in self._config.conf.password["is_secure"]["must_not"]:
            if re.search(must_not, password):
                return PasswordReviewMessages.ErrorTypes.PasswordMustNot

        return PasswordReviewMessages.SuccessfulTypes.Successful
        
    def load_password(self, password: str, salt: bytes = None):
        if salt is None:
            salt = bcrypt.gensalt(12)

        self.salt = salt

        report: PasswordReviewMessages.ErrorTypes or PasswordReviewMessages.SuccessfulTypes = self._validation_is(
            password=password
        )

        if report.IsPositive:
            self.password = password
            self._hash = self._gen_hash()
        else:
            raise report(report.Message)

    def gen_password(self, length: int = 32, pool: str = None, salt: bytes = None):
        if pool is None:
            pool = string.ascii_letters + string.punctuation + string.digits
        if salt is None:
            salt = bcrypt.gensalt(12)

        self.salt = salt
        self.pool = pool
        self.length = length

        self.password = self._gen_passwd()
        self._hash = self._gen_hash()

    def verify(self, password: str = None, passwordHash: str = None) -> bool:
        if password is not None:
            try:
                password_hash = self._hash.encode('utf-8')

                return bcrypt.checkpw(self._get_simple_password_hash(password=password), password_hash)
            except AttributeError:
                raise ValueError("There is no _hash value of the password. You may have to generate a password first.")
        else:
            password = base64.b64encode(hashlib.sha256(self.password.encode('utf-8')).digest())
            return bcrypt.checkpw(password=password, hashed_password=passwordHash.encode('utf-8'))

    def get_hash(self) -> str:
        return self._hash

    def _gen_hash(self) -> str:
        hashed = bcrypt.hashpw(
            password=self._get_simple_password_hash(password=self.password),
            salt=self.salt
        )

        return hashed.decode()

    def _similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio() * 100

    def passwordRegulationsAreObserved(
            self, similarityComparison: str = None,
            maximumOverTuning: int or float = 80.0
    ) -> bool:
        passwordRegulationIsRespected = re.match(r'[A-Za-z0-9@#$%^&+=]{12,}', self.password) is not None
        if similarityComparison is not None:
            simCom = self._similar(self.password, similarityComparison) <= maximumOverTuning
            return simCom and passwordRegulationIsRespected
        else:
            return passwordRegulationIsRespected

    def _gen_passwd(self) -> str:
        return ''.join(random.choices(self.pool, k=self.length))

    def _get_simple_password_hash(self, password: str) -> bytes:
        return base64.b64encode(hashlib.sha256(password.encode('utf-8')).digest())

    def __str__(self) -> str:
        return self.description


# Password Example:
if __name__ == "__main__":
    p = Password(description="An example password", passwordType=PasswordType.UserPassword,
                 configuration=Configuration(
                     path="../../../server/backend/config/Configuration.yaml",
                     configPaths=False
                 ).load())

    # p.load_password("Ab12*€Cd")
    p.load_password("393G7k2&")
    print(p.password)
    print(p.get_hash())

    pwd = p.password

    if p.verify(password=pwd):
        print(f"Password >> {pwd} << is correct")
    else:
        print(f"Password >> {pwd} << is incorrect")
