from datetime import datetime
import tarfile
import requests
import json
import logging
import os
from mindlakesdk.utils import ResultType
import minddatapack.utils

class IPFSConnector(minddatapack.utils.Connector):
    def __init__(self, apiEndpoint: str = None, apiKey: str = None, apiSecret: str = None):
        self.apiEndpoint = apiEndpoint
        if not self.apiEndpoint:
            self.apiEndpoint = 'http://localhost:5001'
        self.apiKey = apiKey
        self.apiSecret = apiSecret

    def save(self, dataPack: "minddatapack.DataPack", fileName: str) -> ResultType:
        result = dataPack._saveToLocalFile(fileName)
        if not result:
            return result
        metaFileName = fileName + minddatapack.utils.METADATA_EXT
        try:
            csvFile = open(fileName, 'rb')
            metaFile = open(metaFileName, 'rb')
            files = {}
            files[fileName] = csvFile
            files[metaFileName] = metaFile
            if self.apiKey and self.apiSecret:
                response = requests.post(self.apiEndpoint + '/api/v0/add?pin=true&wrap-with-directory=true', files=files, auth=(self.apiKey,self.apiSecret))
            else:
                response = requests.post(self.apiEndpoint + '/api/v0/add?pin=true&wrap-with-directory=true', files=files)
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

    def load(self, dataPack: "minddatapack.DataPack", ipfsCID: str) -> ResultType:
        cacheTarFileName = minddatapack.utils.CACHE_PREFIX + datetime.now().strftime("%Y%m%d%H%M%S%f") + '.tar.gz'
        metaFileName = None
        dataFileName = None
        try:
            if self.apiKey and self.apiSecret:
                response = requests.post(self.apiEndpoint + f'/api/v0/get?arg={ipfsCID}&archive=true&compress=true&compression-level=6', auth=(self.apiKey,self.apiSecret))
            else:
                response = requests.post(self.apiEndpoint + f'/api/v0/get?arg={ipfsCID}&archive=true&compress=true&compression-level=6')
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
                    return dataPack._loadFromLocalFile(dataFileName)
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
