name = "minddatapack"

import mindlakesdk
from mindlakesdk.utils import ResultType, DataType
from web3 import Web3
import importlib.metadata
from minddatapack.arweaveconnector import ArweaveConnector
from minddatapack.ipfsconnector import IPFSConnector
from minddatapack.web3storageconnector import Web3StorageConnector
import minddatapack.mindlakeconnector
import minddatapack.localfileconnector
from minddatapack.utils import Column, Connector

class DataPack:
    DataType = DataType
    Column = Column
    IPFSConnector = IPFSConnector
    Web3StorageConnector = Web3StorageConnector
    ArweaveConnector = ArweaveConnector
    LocalFileConnector = minddatapack.localfileconnector.LocalFileConnector
    MindLakeConnector = minddatapack.mindlakeconnector.MindLakeConnector

    def __init__(self, walletPrivateKey: str):
        self.existData = False
        self.__columns = None
        self.data = None
        self.columnName = None
        self.fileName = None
        # self.primaryKey = None
        try:
            self.version = importlib.metadata.version('minddatapack')
        except:
            self.version = '0.0.0'
        web3 = Web3(Web3.HTTPProvider(mindlakesdk.settings.WEB3API))
        self.__walletAccount = web3.eth.account.from_key(walletPrivateKey)

    def saveTo(self, connector: Connector, name: str) -> ResultType:
        return connector.save(self, name)
    
    def loadFrom(self, connector: Connector, identifier: str) -> ResultType:
        return connector.load(self, identifier)
    
    def _loadFromMindByQuery(self, sqlStatement: str, mindLake: mindlakesdk.MindLake) -> ResultType:
        result, self.__columns = minddatapack.mindlakeconnector.loadFromMindByQuery(self, sqlStatement, mindLake)
        return result
    
    def _saveToMindLake(self, tableName: str, mindLake: mindlakesdk.MindLake) -> ResultType:
        return minddatapack.mindlakeconnector.saveToMindLake(tableName, mindLake, self.data, self.__columns)

    def _saveToLocalFile(self, filePath: str, ignoreEncrypt: bool = False):
        return minddatapack.localfileconnector.saveToLocalFile(self, filePath, ignoreEncrypt, self.__columns, self.__walletAccount)

    def _loadFromLocalFile(self, filePath: str):
        result, self.__columns = minddatapack.localfileconnector.loadFromLocalFile(self, filePath, self.__walletAccount)
        return result

    def _loadFromCSVFileByDefineColumn(self, csvFilePath: str, columns: list):
        self.__columns = columns
        return minddatapack.localfileconnector.loadFromCSVFileByDefineColumn(self, csvFilePath, columns)
    