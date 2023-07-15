import mindlakesdk
from mindlakesdk.utils import ResultType, DataType
from mindlakesdk.datalake import DataLake

METADATA_EXT = '.meta.json'

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