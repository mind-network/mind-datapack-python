import mindlakesdk
from mindlakesdk.utils import ResultType, DataType
from mindlakesdk.datalake import DataLake
from abc import ABC, abstractmethod

METADATA_EXT = '.meta.json'
CACHE_PREFIX = 'datapack_cache_'

class Column(DataLake.Column):
    def __init__(self, columnName: str, dataType: DataType, encrypt: bool, dataKey: bytes = None):
        super().__init__(columnName, dataType, encrypt)
        if encrypt:
            if dataKey:
                self.dataKey = dataKey
            else:
                self.dataKey = mindlakesdk.utils.genAESKey()
        else:
            self.dataKey = None

class Connector(ABC):
    @abstractmethod
    def __init__(self):
        raise NotImplementedError

    @abstractmethod
    def save(self, dataPack, name: str) -> ResultType:
        raise NotImplementedError

    @abstractmethod
    def load(self, dataPack, identifier: str) -> ResultType:
        raise NotImplementedError