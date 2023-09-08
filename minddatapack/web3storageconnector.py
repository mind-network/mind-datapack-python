from datetime import datetime
import zipfile
import requests
import json
import logging
import os
from mindlakesdk.utils import ResultType
import minddatapack.utils

class Web3StorageConnector(minddatapack.utils.Connector):
    def __init__(self, apiToken: str = None):
        self.apiToken = apiToken

    def save(self, dataPack: "minddatapack.DataPack", fileName: str) -> ResultType:
        cacheZipFileName = minddatapack.utils.CACHE_PREFIX + datetime.now().strftime("%Y%m%d%H%M%S%f") + '.zip'
        result = dataPack._saveToLocalFile(fileName)
        if not result:
            return result
        metaFileName = fileName + minddatapack.utils.METADATA_EXT
        try:
            with zipfile.ZipFile(cacheZipFileName, 'w') as zip:
                zip.write(fileName)
                zip.write(metaFileName)
            zipFile = open(cacheZipFileName, 'rb')
            files = [
                ('file', (cacheZipFileName, zipFile, 'application/zip'))
            ]
            headers = {
                "Authorization": "Bearer " + self.apiToken
            }
            response = requests.post('https://api.web3.storage/upload', headers=headers, files=files)
            if response and response.status_code == 200:
                ipfsHash = json.loads(response.text)['cid']
                return ResultType(0, "Success", ipfsHash)
            else:
                return ResultType(60001, "Network error", None)
        except Exception as e:
            logging.debug("Exception:", str(e))
            return ResultType(60014, "Fail to connect to IPFS", None)
        finally:
            if os.path.exists(fileName):
                os.remove(fileName)
            if os.path.exists(metaFileName):
                os.remove(metaFileName)
            if os.path.exists(cacheZipFileName):
                os.remove(cacheZipFileName)

    def load(self, dataPack: "minddatapack.DataPack", ipfsCID: str):
        cacheZipFileName = minddatapack.utils.CACHE_PREFIX + datetime.now().strftime("%Y%m%d%H%M%S%f") + '.zip'
        metaFileName = None
        dataFileName = None
        try:
            response = requests.get("https://w3s.link/ipfs/" + ipfsCID, stream=True)
            if response and response.status_code == 200:
                with open(cacheZipFileName, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=1024*64):
                        file.write(chunk)
                with zipfile.ZipFile(cacheZipFileName, "r") as zip:
                    fileNames = zip.namelist()
                    if len(fileNames) != 2:
                        return ResultType(60015, "Invalid DataPack data", None)
                    for fileName in fileNames:
                        if fileName.endswith(minddatapack.utils.METADATA_EXT):
                            metaFileName = fileName
                        elif fileName.endswith('.csv'):
                            dataFileName = fileName
                    if metaFileName != dataFileName + minddatapack.utils.METADATA_EXT:
                        return ResultType(60015, "Invalid DataPack data", None)
                    zip.extractall()
                    return dataPack._loadFromLocalFile(dataFileName)
            else:
                return ResultType(60001, "Network error", None)
        except Exception as e:
            logging.debug("Exception:", str(e))
            return ResultType(60014, "Fail to connect to IPFS", None)
        finally:
            if os.path.exists(cacheZipFileName):
                os.remove(cacheZipFileName)
            if dataFileName and os.path.exists(dataFileName):
                os.remove(dataFileName)
            if metaFileName and os.path.exists(metaFileName):
                os.remove(metaFileName)
            if os.path.exists(ipfsCID):
                os.rmdir(ipfsCID)
