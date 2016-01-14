# DictMySQL [![Build Status](https://travis-ci.org/ligyxy/DictMySQL.svg?branch=master)](https://travis-ci.org/ligyxy/DictMySQL)

PyPI page: [https://pypi.python.org/pypi/dictmysql](https://pypi.python.org/pypi/dictmysql)

Documentation: [https://ligyxy.github.io/DictMySQL](https://ligyxy.github.io/DictMySQL)

## Introduction
A mysql class on the top of [PyMySQL](https://github.com/PyMySQL/PyMySQL), for more convenient database manipulation with Python dictionary.

DictMySQL simplifies and unifies the input/output of MySQL queries, by allowing passing values and conditions in dictionary into database. With DictCursor, you can even have a dict-in, dict-out mysql connector.

To install:
```bash
pip install dictmysql
```

Quick example:
```python
from dictmysql import DictMySQL
db = DictMySQL(db='occupation', host='127.0.0.1', user='root', passwd='')

db.select(table='jobs',
          columns=['id','value'],
          where={'$OR': [{'value': {'$LIKE': 'Artist%'}}, {'id': 10}]})
# SELECT `id`, `value` FROM `jobs` WHERE (`value` LIKE "Artist%") OR (`id` = 10);
```

## License

DictMySQL uses the MIT license, see `LICENSE` file for the details.
