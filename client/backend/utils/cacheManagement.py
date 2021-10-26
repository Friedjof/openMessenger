# Friedjof Noweck
# 21.08.2021 Sa
import yaml

from core.utils.backend.configuration import Configuration


class CacheManager:
    def __init__(self, configuration: Configuration, path: str = None):
        self._config = configuration

        if path is None:
            self.cachePath: str = self._config.configPaths.paths["cache"]
        else:
            self.cachePath: str = path

    def read(self) -> dict:
        with open(self.cachePath, "r") as cacheFile:
            cache: dict = yaml.safe_load(cacheFile)
        if cache is not None:
            return cache
        else:
            return {}

    def write(self, cache: dict) -> bool:
        with open(self.cachePath, 'w+') as cacheFile:
            try:
                yaml.dump(cache, cacheFile, allow_unicode=True)
                return True
            except yaml.YAMLError as exc:
                print(exc)
                return False

    def clear(self):
        pass
