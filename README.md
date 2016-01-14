# DictMySQL [![Build Status](https://travis-ci.org/ligyxy/DictMySQL.svg?branch=master)](https://travis-ci.org/ligyxy/DictMySQL)
A mysql class on the top of [PyMySQL](https://github.com/PyMySQL/PyMySQL), for more convenient database manipulation, especially with Python dictionary.

DictMySQL simplifies and unifies the input/output of MySQL queries for you, by allowing using dictionary to pass in values and conditions into MySQL. With DictCursor, you can even have a dict-in, dict-out db connector.

```python
from DictMySQL import DictMySQL
db = DictMySQL(db='occupation', host='127.0.0.1', passwd='', user='root')

db.select(table='jobs',
          columns=['id','value'],
          where={'$OR': [{'value': {'$LIKE': 'Artist%'}}, {'id': 10}]})
# SELECT `id`, `value` FROM `jobs` WHERE (`value` LIKE "Artist%") OR (`id` = 10);
```
