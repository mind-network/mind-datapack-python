import mindlakesdk
from mindlakesdk.utils import ResultType, DataType
import minddatapack.utils

def loadFromMindByQuery(dataPack, sqlStatement: str, mindLake: mindlakesdk.MindLake) -> ResultType:
    result = mindLake.datalake.queryForDataAndMeta(sqlStatement)
    if not result:
        return result
    columnRefs = result.data['columnRefs']
    columns = []
    nameCount = {}
    dataPack.columnName = []
    for index, column in enumerate(columnRefs):
        # It's possible to get some duplicate column name in queries containing calculation
        # rename duplicate column name
        if column['name'] in nameCount:
            nameCount[column['name']] += 1
            column['name'] = f"{column['name']}_{nameCount[column['name']]}"
        else:
            nameCount[column['name']] = 0
        columnMeta = minddatapack.utils.Column(column['name'], DataType(column['type']), column['enc'])
        dataPack.columnName.append(column['name'])
        columns.append(columnMeta)

    dataPack.data = []
    for row in result.data['data']:
        rowResult = []
        for index, cell in enumerate(row):
            if columns[index].encrypt:
                decryptResult = mindLake.cryptor.decrypt(cell)
                if not decryptResult:
                    return decryptResult
                rowResult.append(decryptResult.data)
            else:
                rowResult.append(cell)
        dataPack.data.append(rowResult)
    dataPack.existData = True
    return ResultType(0, 'Success'), columns

def saveToMindLake(tableName: str, mindLake: mindlakesdk.MindLake, data, columns) -> ResultType:
    result = mindLake.datalake.createTable(tableName, columns)
    if not result:
        return result
    for row in data:
        insert_value = ""
        for index, cell in enumerate(row):
            column = columns[index]
            if column.encrypt:
                encryptResult = mindLake.cryptor.encrypt(cell, tableName+'.'+column.columnName)
                if not encryptResult:
                    return encryptResult
                insert_value = insert_value + "'" + encryptResult.data + "',"
            else:
                if column.type == DataType.text or column.type == DataType.timestamp:
                    insert_value = insert_value + "'" + str(cell) + "',"
                else:
                    insert_value = insert_value + str(cell) + ","
        result = mindLake.datalake.query(f'INSERT INTO "{tableName}" VALUES ({insert_value[:-1]})')
        if not result:
            return result
    return ResultType(0, 'Success')
