import csv
import datetime
from decimal import Decimal
import json
import os
import base64
import logging
import struct
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
from nacl.public import Box, PrivateKey, PublicKey
import mindlakesdk
from mindlakesdk.utils import ResultType, DataType
import minddatapack.utils

def __encrypt(data, columnMeta: minddatapack.utils.Column) -> ResultType:
    try:
        data = __encodeByDataType(data, columnMeta.type)
        checkCode = __genCheckCode(data, 1)
        data_to_enc = data + checkCode
        iv = get_random_bytes(16)
        encrypted_data = mindlakesdk.utils.aesEncrypt(columnMeta.dataKey, iv, data_to_enc)
        buf = iv + encrypted_data
        checkCode2 = __genCheckCode(buf, 1)
        result = checkCode2 + buf
        resultHex = '\\x' + result.hex()
    except Exception as e:
        logging.debug("Exception:", str(e))
        return ResultType(60012, 'Encrypt data failed')
    return ResultType(0, "Success", resultHex)

def __decrypt(cipher: str, columnMeta: minddatapack.utils.Column) -> ResultType:
    try:
        cipher = cipher[2:]
        cipher = bytes.fromhex(cipher)
        checkCode = cipher[:1]
        cipher = cipher[1:]
        iv = cipher[:16]
        cipher = cipher[16:]
        data = mindlakesdk.utils.aesDecrypt(columnMeta.dataKey, iv, cipher)
        checkCode = data[-1:]
        data = data[:-1]
        checkCode2 = __genCheckCode(data, 1)
        if checkCode != checkCode2:
            return ResultType(60013, 'Check code not match')
        data = __decodeByDataType(data, columnMeta.type)
    except Exception as e:
        logging.debug("Exception:", str(e))
        return ResultType(60013, 'Decrypt data failed')
    return ResultType(0, "Success", data)

def saveToLocalFile(dataPack, filePath: str, ignoreEncrypt: bool, columns: list, walletAccount):
    if not dataPack.existData:
        return ResultType(60006, 'No data in DataPack')
    dataPack.fileName = os.path.basename(filePath)
    with open(filePath, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(dataPack.columnName)
        if ignoreEncrypt:
            for row in dataPack.data:
                writer.writerow(row)
        else:
            for row in dataPack.data:
                rowEncrypted = []
                for index, cell in enumerate(row):
                    if columns[index].encrypt:
                        encryptResult = __encrypt(cell, columns[index])
                        if not encryptResult:
                            return encryptResult
                        rowEncrypted.append(encryptResult.data)
                    else:
                        rowEncrypted.append(cell)
                writer.writerow(rowEncrypted)

    sha256_hash = SHA256.new()
    with open(filePath, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            sha256_hash.update(chunk)
    sha256_hash_hex = sha256_hash.hexdigest()

    metadata = __buildMetadata(dataPack.fileName, ignoreEncrypt, sha256_hash_hex, columns, walletAccount)
    with open(filePath+minddatapack.utils.METADATA_EXT, 'w') as file:
        json.dump(metadata, file)
    return ResultType(0, None)

def __buildMetadata(fileName: str, ignoreEncrypt: bool, fileHash: str, columns: list, walletAccount) -> dict:
    metadata = {}
    metadata['FileName'] = fileName
    metadata['IgnoreEncrypt'] = ignoreEncrypt
    metadata['FileHash'] = fileHash
    metadata['Column'] = []
    for column in columns:
        columnMeta = {}
        columnMeta['ColumnName'] = column.columnName
        columnMeta['DataType'] = column.type.name
        columnMeta['Encrypt'] = column.encrypt
        if column.encrypt:
            dk = column.dataKey
            dkEnc = __encryptWithWalletKey(walletAccount, dk)
            dkEncBase64 = base64.b64encode(dkEnc).decode()
            columnMeta['DataKeyCipher'] = dkEncBase64
        metadata['Column'].append(columnMeta)
    return metadata

def loadFromLocalFile(dataPack, filePath: str, walletAccount):
    # the path of the meta file should be filePath + '.meta.json'
    metaFilePath = filePath + minddatapack.utils.METADATA_EXT
    if not os.path.exists(filePath):
        return ResultType(60007, 'CSV File not found')
    if not os.path.exists(metaFilePath):
        return ResultType(60008, 'Metadata file not found')
    with open(metaFilePath, 'r') as file:
        metadata = json.load(file)
        dataPack.fileName = metadata['FileName']
        ignoreEncrypt = metadata['IgnoreEncrypt']
        columns = []
        for column in metadata['Column']:
            if column['Encrypt']:
                dkEncBase64 = column['DataKeyCipher']
                dkEnc = base64.b64decode(dkEncBase64)
                dk = __decryptWithWalletKey(walletAccount, dkEnc)
                columnMeta = minddatapack.utils.Column(column['ColumnName'], DataType[column['DataType']], column['Encrypt'], dk)
            else:
                columnMeta = minddatapack.utils.Column(column['ColumnName'], DataType[column['DataType']], column['Encrypt'])
            columns.append(columnMeta)
    with open(filePath, 'r') as file:
        reader = csv.reader(file)
        dataPack.columnName = next(reader)
        dataPack.data = []
        for row in reader:
            rowDecrypted = []
            for index, cell in enumerate(row):
                if not ignoreEncrypt and columns[index].encrypt:
                    decryptResult = __decrypt(cell, columns[index])
                    if not decryptResult:
                        return decryptResult
                    rowDecrypted.append(decryptResult.data)
                else:
                    if columns[index].type == DataType.int4 or columns[index].type == DataType.int8:
                        rowDecrypted.append(int(cell))
                    elif columns[index].type == DataType.float4 or columns[index].type == DataType.float8:
                        rowDecrypted.append(float(cell))
                    elif columns[index].type == DataType.decimal:
                        rowDecrypted.append(Decimal(cell))
                    elif columns[index].type == DataType.timestamp:
                        rowDecrypted.append(datetime.datetime.strptime(cell, '%Y-%m-%d %H:%M:%S.%f'))
                    else:
                        rowDecrypted.append(cell)
            dataPack.data.append(rowDecrypted)
        dataPack.existData = True
    return ResultType(0, "Success"), columns

def loadFromCSVFileByDefineColumn(dataPack, csvFilePath: str, columns: list):
    # the whole csv file should be in plain text
    if not os.path.exists(csvFilePath):
        return ResultType(60007, 'CSV File not found')
    columnNameList = []
    for column in columns:
        if not isinstance(column, minddatapack.utils.Column):
            return ResultType(60009, 'Invalid column definition')
        else:
            if column.columnName in columnNameList:
                return ResultType(60011, 'Duplicate column name')
            columnNameList.append(column.columnName)
    with open(csvFilePath, 'r') as file:
        reader = csv.reader(file)
        columnInCSV = next(reader)
        if columnInCSV != columnNameList:
            return ResultType(60010, 'Column name in CSV file does not match with column definition')
        dataPack.data = []
        for row in reader:
            formattedRow = []
            for index, cell in enumerate(row):
                if columns[index].type == DataType.int4 or columns[index].type == DataType.int8:
                    formattedRow.append(int(cell))
                elif columns[index].type == DataType.float4 or columns[index].type == DataType.float8:
                    formattedRow.append(float(cell))
                elif columns[index].type == DataType.decimal:
                    formattedRow.append(Decimal(cell))
                elif columns[index].type == DataType.timestamp:
                    formattedRow.append(datetime.datetime.strptime(cell, '%Y-%m-%d %H:%M:%S.%f'))
                else:
                    formattedRow.append(cell)
            dataPack.data.append(formattedRow)
    dataPack.existData = True
    return ResultType(0, "Success")

def __encryptWithWalletKey(walletAccount, msg):
    ephemeralPrivKey = PrivateKey.generate()
    privKey = PrivateKey(walletAccount.key)
    pubKey = privKey.public_key
    encryptBox = Box(ephemeralPrivKey, pubKey)
    nounce = get_random_bytes(24)
    msg = base64.b64encode(msg)
    encryptedMsg = encryptBox.encrypt(msg, nounce)
    return bytes(ephemeralPrivKey.public_key) + nounce + encryptedMsg.ciphertext

def __decryptWithWalletKey(walletAccount, data):
    privKey = PrivateKey(walletAccount.key)
    ephemeralPubKey, nounce, ciphertext = data[:32], data[32:56], data[56:]
    box = Box(privKey, PublicKey(ephemeralPubKey))
    return base64.b64decode(box.decrypt(ciphertext, nounce))

def __encodeByDataType(data, dataType: DataType) -> bytes:
    if dataType == DataType.int4:
        result = struct.pack("<i", data)
    elif dataType == DataType.int8:
        result = struct.pack("<q", data)
    elif dataType == DataType.float4:
        result = struct.pack("<f", data)
    elif dataType == DataType.float8:
        result = struct.pack("<d", data)
    elif dataType == DataType.decimal:
        val = Decimal(data)
        val_str = str(val)
        result = val_str.encode('utf-8')
    elif dataType == DataType.text:
        result = data.encode('utf-8')
    elif dataType == DataType.timestamp:
        u_sec = int(data.timestamp() * 1000000)
        u_sec -= 946684800000000
        u_sec += int(datetime.datetime.now().astimezone().utcoffset().total_seconds() * 1000000)
        result = struct.pack('<q', u_sec)
    else:
        raise Exception("Unsupported encryption type")
    return result

def __decodeByDataType(data: bytes, dataType: DataType):
    if dataType == DataType.int4:
        size = struct.calcsize('<i')
        buf = data[:size]
        result = struct.unpack('<i', buf)[0]
    elif dataType == DataType.int8:
        size = struct.calcsize('<q')
        buf = data[:size]
        result = struct.unpack('<q', buf)[0]
    elif dataType == DataType.float4:
        size = struct.calcsize('<f')
        buf = data[:size]
        result = struct.unpack('<f', buf)[0]
    elif dataType == DataType.float8:
        size = struct.calcsize('<d')
        buf = data[:size]
        result = struct.unpack('<d', buf)[0]
    elif dataType == DataType.decimal:
        result = Decimal(data.decode('utf-8'))
    elif dataType == DataType.text:
        result = data.decode('utf-8')
    elif dataType == DataType.timestamp:
        size = struct.calcsize('<q')
        buf = data[:size]
        u_sec = struct.unpack('<q', buf)[0]
        u_sec += 946684800000000
        u_sec -= int(datetime.datetime.now().astimezone().utcoffset().total_seconds() * 1000000)
        time_stamp = u_sec / 1000000.0
        result = datetime.datetime.fromtimestamp(time_stamp)
    else:
        raise Exception("Unsupported encryption type")
    return result

def __genCheckCode(data: bytes, resultSize):
    tmpCode = bytearray(resultSize)
    for i in range(len(data)):
        n = i % resultSize
        tmpCode[n] ^= data[i]
    return bytes(tmpCode)
