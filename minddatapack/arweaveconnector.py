import json
import os
import logging
import requests
from mindlakesdk.utils import ResultType
import minddatapack.utils

def saveToArweave(dataPack, fileName: str, tokenName: str, arWalletFile: str, ethWalletPrivateKey: str):
    result = dataPack.saveToLocalFile(fileName)
    if not result:
        return result
    dataFileName = fileName
    metaFileName = fileName + minddatapack.utils.METADATA_EXT
    try:
        import arseeding, everpay
        if arWalletFile:
            signer = everpay.ARSigner(arWalletFile)
        else:
            signer = everpay.ETHSigner(ethWalletPrivateKey)
        with open(dataFileName, 'rb') as dataFile:
            with open(metaFileName, 'r') as metaFile:
                data = dataFile.read()
                metadata = metaFile.read()
                order = arseeding.send_and_pay(signer, tokenName, data, tags= [
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

def loadFromArweave(dataPack, id: str, arGateway: str):
    metaFileName = None
    dataFileName = None
    try:
        if arGateway[-1] != '/':
            arGateway += '/'
        metaUrl = arGateway + 'bundle/tx/' + id
        metaResponse = requests.get(metaUrl)
        if metaResponse and metaResponse.status_code == 200:
            txMeta = json.loads(metaResponse.text)
            metadataJsonStr = txMeta['tags'][1]['value']
            metadata = json.loads(metadataJsonStr)
            dataFileName = metadata['FileName']
            metaFileName = dataFileName + minddatapack.utils.METADATA_EXT
            with open(metaFileName, 'wb') as file:
                file.write(metadataJsonStr.encode('utf-8'))
            
            dataUrl = arGateway + id
            dataResponse = requests.get(dataUrl)
            if dataResponse and dataResponse.status_code == 200:
                with open(dataFileName, 'wb') as file:
                    file.write(dataResponse.content)

            return dataPack.loadFromLocalFile(dataFileName)
        else:
            return ResultType(60001, "Network error", None)
    except Exception as e:
        logging.debug("Exception:", str(e))
        return ResultType(60014, "Fail to connect to Arweave", None)
    finally:
        if dataFileName and os.path.exists(dataFileName):
            os.remove(dataFileName)
        if metaFileName and os.path.exists(metaFileName):
            os.remove(metaFileName)
