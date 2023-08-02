name = "minddatapack"

import mindlakesdk
from mindlakesdk.utils import ResultType, DataType
from web3 import Web3
import importlib.metadata
import minddatapack.arweaveconnector
import minddatapack.mindlakeconnector
import minddatapack.localfileconnector
import minddatapack.ipfsconnector
from minddatapack.utils import Column

class DataPack:
    DataType = DataType
    Column = Column

    def __init__(self, walletPrivateKey: str):
        self.existData = False
        self.__columns = None
        self.data = None
        self.columnName = None
        self.fileName = None
        self.primaryKey = None
        self.version = importlib.metadata.version('minddatapack')
        self.__walletPrivateKey = walletPrivateKey
        web3 = Web3(Web3.HTTPProvider(mindlakesdk.settings.WEB3API))
        self.__walletAccount = web3.eth.account.from_key(walletPrivateKey)

    def loadFromMindByQuery(self, sqlStatement: str, mindLake: mindlakesdk.MindLake) -> ResultType:
        result, self.__columns = minddatapack.mindlakeconnector.loadFromMindByQuery(self, sqlStatement, mindLake)
        return result
    
    def saveToMindLake(self, tableName: str, mindLake: mindlakesdk.MindLake) -> ResultType:
        return minddatapack.mindlakeconnector.saveToMindLake(tableName, mindLake, self.data, self.__columns)

    def saveToLocalFile(self, filePath: str, ignoreEncrypt: bool = False):
        return minddatapack.localfileconnector.saveToLocalFile(self, filePath, ignoreEncrypt, self.__columns, self.__walletAccount)

    def loadFromLocalFile(self, filePath: str):
        result, self.__columns = minddatapack.localfileconnector.loadFromLocalFile(self, filePath, self.__walletAccount)
        return result

    def loadFromCSVFileByDefineColumn(self, csvFilePath: str, columns: list):
        self.__columns = columns
        return minddatapack.localfileconnector.loadFromCSVFileByDefineColumn(self, csvFilePath, columns)

    def saveToArweave(self, fileName: str, tokenName: str, arWalletFile: str = None):
        return minddatapack.arweaveconnector.saveToArweave(self, fileName, tokenName, arWalletFile, self.__walletPrivateKey)

    def loadFromArweave(self, id: str, arGateway: str = 'https://arseed.web3infra.dev/'):
        return minddatapack.arweaveconnector.loadFromArweave(self, id, arGateway)

    def saveToIPFS(self, fileName: str, apiEndpoint: str = 'http://localhost:5001', apiKey: str = None, apiSecret: str = None):
        return minddatapack.ipfsconnector.saveToIPFS(self, fileName, apiEndpoint, apiKey, apiSecret)

    def loadFromIPFS(self, ipfsCID: str, apiEndpoint: str = 'http://localhost:5001', apiKey: str = None, apiSecret: str = None):
        return minddatapack.ipfsconnector.loadFromIPFS(self, ipfsCID, apiEndpoint, apiKey, apiSecret)
