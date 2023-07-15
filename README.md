# Mind DataPack Python SDK

An Python implementation for Mind DataPack

## Description

Mind Network is a permissionless and scalable zero-trust data lake. Its core feature is to compute over encrypted data and allow that data to be stored in various Web3 storage protocols. 

DataPack, contributed by the Mind Network Team, is to enable data transformation and transportation between Mind Network and storage protocols, like Arweave. It is an adapter that facilitates the smooth conversion of data between plaintext and ciphertext to be stored in Mind Network or Arweave. This module empowers users to retrieve their infrequently processed data, known as "cold data," from Mind Network and store it in local or decentralized storage. When the need arises to perform computing on the encrypted data again, users can effortlessly load it back into Mind Network for processing.


## Getting Started

### Dependencies

* Python > 3.8
* pip
* mindlakesdk
* arseeding

### Installing

* pip install minddatapack

### Import
```
from minddatapack import DataPack
...
```

### More examples
* [use case of arweave in jupyter](/examples/use_case_arweave.ipynb)

## code
```
mind-datapack-python
|-- minddatapack # source code
|   |-- __init__.py
|   |-- arweaveconnector.py
|   |-- localfileconnector.py
|   |-- mindlakeconnector.py
|   └-- utils.py
|-- examples # use case examples
|-- README.md
└--- LICENSE

```

## Help

Full doc: [https://mind-network.gitbook.io/mind-lake-sdk](https://mind-network.gitbook.io/mind-lake-sdk) 

## Authors
 
* Dennis [@NuIlPtr](https://twitter.com/nuilptr)
* George [@georgemindnet](https://twitter.com/georgemindnet)

## Version History

* v1.0
    * Initial Release

## License

This project is licensed under the [MIT] License - see the LICENSE.md file for details
