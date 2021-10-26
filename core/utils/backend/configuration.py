# Friedjof Noweck
# 18.08.2021 Mi
import yaml
from collections import namedtuple
import time

from core.utils.backend.logging import LoggingStatus, Logging
from core.utils.backend.omUuid import UUID


class ConfigPaths:
    def __init__(self, path: str = "paths.yaml"):
        self.configPathsPath = path

        self.paths: dict = self._load()

    def __getitem__(self, key) -> str:
        return self.paths[key]

    def _load(self) -> dict:
        with open(self.configPathsPath, "r") as conf_path_file:
            paths: dict = yaml.safe_load(conf_path_file)
        return paths

    def reload(self):
        self.paths: dict = self._load()


class Configuration:
    def __init__(self, path: str = None,
                 configPaths: ConfigPaths or bool = None, pathsPath: str = "paths.yaml",
                 logLevel: LoggingStatus.__dict__ = LoggingStatus.DEBUG):
        if configPaths is None:
            self.configPaths = ConfigPaths(path=pathsPath)
        else:
            self.configPaths = configPaths

        if path is None:
            path: str = self.configPaths["config"]

        self.path: str = path
        self._conf_namedtuple: namedtuple = None
        self.conf: namedtuple = None

        self.timestamp = time.time()

        self.log = Logging(configuration=self, logLevel=logLevel)
        self.logStatus = LoggingStatus

        self.uuid = UUID()

    def load(self) -> namedtuple:
        with open(self.path, 'r') as stream:
            try:
                parsed_yaml: dict = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
        self._conf_namedtuple = namedtuple('Configuration', parsed_yaml.keys())
        self.conf = self._conf_namedtuple(**parsed_yaml)

        self.timestamp = time.time()
        return self

    def update(self, config: dict) -> bool:
        with open(self.path, 'w+') as stream:
            try:
                yaml.dump(config, stream, allow_unicode=True)

                self.timestamp = time.time()
                return True
            except yaml.YAMLError as exc:
                print(exc)
                return False

    def __str__(self) -> str:
        try:
            return f"Version: {self.conf.version}"
        except AttributeError:
            raise AttributeError("There is no version number. You may have to load the config first")


if __name__ == "__main__":
    c = Configuration()
    c.load()
    print(c.conf)
    print(c.timestamp)
