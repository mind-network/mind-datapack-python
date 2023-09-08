import json
import os
import logging
import requests
from datetime import datetime
from mindlakesdk.utils import ResultType
import minddatapack.utils

class ArweaveConnector(minddatapack.utils.Connector):
    def __init__(self, tokenName: str = None, arWalletFile: str = None, ethWalletPrivateKey: str = None, arGateway: str = None):
        self.tokenName = tokenName
        self.arWalletFile = arWalletFile
        self.ethWalletPrivateKey = ethWalletPrivateKey
        if arGateway:
            if arGateway[-1] != '/':
                arGateway += '/'
            self.arGateway = arGateway
        else:
            self.arGateway = 'https://arseed.web3infra.dev/'

    def save(self, dataPack: "minddatapack.DataPack", fileName: str) -> ResultType:
        result = dataPack._saveToLocalFile(fileName)
        if not result:
            return result
        dataFileName = fileName
        metaFileName = fileName + minddatapack.utils.METADATA_EXT
        try:
            import arseeding, everpay
            if self.arWalletFile:
                signer = everpay.ARSigner(self.arWalletFile)
            else:
                signer = everpay.ETHSigner(self.ethWalletPrivateKey)
            with open(dataFileName, 'rb') as dataFile:
                with open(metaFileName, 'r') as metaFile:
                    data = dataFile.read()
                    metadata = metaFile.read()
                    order = arseeding.send_and_pay(signer, self.tokenName, data, tags= [
                        {'name': 'App-Name', 'value': 'Mind-DataPack'},
                        {'name': 'MindDataPackMetaData', 'value': metadata},
                        {'name': 'Content-Type', 'value': 'text/csv'}])
                    return ResultType(0, "Success", order['itemId'])
        except Exception as e:
            logging.debug("Exception:", str(e))
            return ResultType(60014, "Fail to connect to Arweave", None)
        finally:
            if os.path.exists(dataFileName):
                os.remove(dataFileName)
            if os.path.exists(metaFileName):
                os.remove(metaFileName)

    def load(self, dataPack: "minddatapack.DataPack", transactionID: str) -> ResultType:
        cacheDataFileName = minddatapack.utils.CACHE_PREFIX + datetime.now().strftime("%Y%m%d%H%M%S%f") + '.csv'
        cacheMetaFileName = cacheDataFileName + minddatapack.utils.METADATA_EXT
        try:
            metaUrl = self.arGateway + 'bundle/tx/' + transactionID
            metaResponse = requests.get(metaUrl)
            if metaResponse and metaResponse.status_code == 200:
                txMeta = json.loads(metaResponse.text)
                for tag in txMeta['tags']:
                    if tag['name'] == 'MindDataPackMetaData':
                        metadataJsonStr = tag['value']
                with open(cacheMetaFileName, 'wb') as file:
                    file.write(metadataJsonStr.encode('utf-8'))
                
                dataUrl = self.arGateway + transactionID
                dataResponse = requests.get(dataUrl)
                if dataResponse and dataResponse.status_code == 200:
                    with open(cacheDataFileName, 'wb') as file:
                        file.write(dataResponse.content)

                return dataPack._loadFromLocalFile(cacheDataFileName)
            else:
                return ResultType(60001, "Network error", None)
        except Exception as e:
            logging.debug("Exception:", str(e))
            return ResultType(60014, "Fail to connect to Arweave", None)
        finally:
            if os.path.exists(cacheDataFileName):
                os.remove(cacheDataFileName)
            if os.path.exists(cacheMetaFileName):
                os.remove(cacheMetaFileName)
