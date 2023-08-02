from datetime import datetime
import tarfile
import requests
import json
import logging
import os
from mindlakesdk.utils import ResultType
import minddatapack.utils


def saveToIPFS(dataPack, fileName: str, apiEndpoint: str, apiKey: str, apiSecret: str) -> ResultType:
    result = dataPack.saveToLocalFile(fileName)
    if not result:
        return result
    metaFileName = fileName + minddatapack.utils.METADATA_EXT
    try:
        csvFile = open(fileName, 'rb')
        metaFile = open(metaFileName, 'rb')
        files = {}
        files[fileName] = csvFile
        files[metaFileName] = metaFile
        if apiKey and apiSecret:
            response = requests.post(apiEndpoint + '/api/v0/add?pin=true&wrap-with-directory=true', files=files, auth=(apiKey,apiSecret))
        else:
            response = requests.post(apiEndpoint + '/api/v0/add?pin=true&wrap-with-directory=true', files=files)
        if response and response.status_code == 200:
            folderJson = response.text.splitlines()[-1]
            ipfsHash = json.loads(folderJson)['Hash']
            return ResultType(0, "Success", ipfsHash)
        else:
            return ResultType(60001, "Network error", None)
    except Exception as e:
        logging.debug("Exception:", str(e))
        return ResultType(60014, "Fail to connect to IPFS", None)
    finally:
        if csvFile:
            csvFile.close()
        if metaFile:
            metaFile.close()
        if os.path.exists(fileName):
            os.remove(fileName)
        if os.path.exists(metaFileName):
            os.remove(metaFileName)

def loadFromIPFS(dataPack, ipfsCID: str, apiEndpoint: str, apiKey: str, apiSecret: str):
    cacheTarFileName = minddatapack.utils.CACHE_PREFIX + datetime.now().strftime("%Y%m%d%H%M%S%f") + '.tar.gz'
    metaFileName = None
    dataFileName = None
    try:
        if apiKey and apiSecret:
            response = requests.post(apiEndpoint + f'/api/v0/get?arg={ipfsCID}&archive=true&compress=true&compression-level=6', auth=(apiKey,apiSecret))
        else:
            response = requests.post(apiEndpoint + f'/api/v0/get?arg={ipfsCID}&archive=true&compress=true&compression-level=6')
        if response and response.status_code == 200:
            with open(cacheTarFileName, 'wb') as file:
                file.write(response.content)
            with tarfile.open(cacheTarFileName, "r:gz") as tar:
                members = tar.getmembers()
                if len(members) != 3:
                    return ResultType(60015, "Invalid DataPack data", None)
                for member in members:
                    nameSplit = member.name.split('/')
                    if len(nameSplit) == 2:
                        if member.name.endswith(minddatapack.utils.METADATA_EXT):
                            metaFileName = member.name
                        elif member.name.endswith('.csv'):
                            dataFileName = member.name
                        tar.extract(member)
                if metaFileName != dataFileName + minddatapack.utils.METADATA_EXT:
                    return ResultType(60015, "Invalid DataPack data", None)
                return dataPack.loadFromLocalFile(dataFileName)
        else:
            return ResultType(60001, "Network error", None)
    except Exception as e:
        logging.debug("Exception:", str(e))
        return ResultType(60014, "Fail to connect to IPFS", None)
    finally:
        if os.path.exists(cacheTarFileName):
            os.remove(cacheTarFileName)
        if dataFileName and os.path.exists(dataFileName):
            os.remove(dataFileName)
        if metaFileName and os.path.exists(metaFileName):
            os.remove(metaFileName)
        if os.path.exists(ipfsCID):
            os.rmdir(ipfsCID)
