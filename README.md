# DictMySQLdb [![Build Status](https://travis-ci.org/ligyxy/DictMySQLdb.svg?branch=master)](https://travis-ci.org/ligyxy/DictMySQLdb)
A mysql package on the top of [MySQL-python](http://mysql-python.sourceforge.net/MySQLdb.html, "MySQL-python") or [PyMySQL](https://github.com/PyMySQL/PyMySQL, "PyMySQL") for more convenient database manipulation with Python dictionary. It uses MySQL-python for Python 2 and PyMySQL for Python 3 as connector.

DictMySQLdb simplifies and unifies the input/output of MySQL queries for you, by allowing using dictionary to pass in values and conditions into MySQL. With DictCursor, you can even have a dict-in, dict-out db connector.

```python
from dictmysqldb import DictMySQLdb
db = DictMySQLdb(db='occupation', host='127.0.0.1', passwd='', user='root')

db.select(tablename='jobs', field=['id','value'], where={'$OR': [{'value': {'$=': 'Artist'}}, {'id': 10}]})
```

```sql
SELECT `id`, `value` FROM `jobs` WHERE `id` = 10 OR `value` = "Artist";
```

Besides of the methods that MySQL-python or PyMySQL offers, DictMySQLdb provides the following methods:

* `query()`
* `insert()`
* `insertmany()`
* `upsert()`
* `get()`
* `update()`
* `select()`
* `delete()`
* `now()`
* `last_insert_id()`

## Examples

Creating connection:

	from dictmysqldb import DictMySQLdb
	db = DictMySQLdb(db='occupation', 
	                 host='127.0.0.1', 
	                 passwd='', 
	                 user='root',
	                 port=3306,
	                 charset='utf8',
	                 init_command='SET NAMES UTF8',
	                 dictcursor=False)
	
Fetching one record:

	db.get(tablename='jobs', condition={'id': 2}, field='value')
	# u'FACULTY'
	# SELECT `value` FROM `jobs` WHERE `id` = 2 LIMIT 1

Passing in multiple conditions:
				  
	db.select(tablename='jobs', 
			  condition={'id': (2, 3), 'sanitized': None},
			  field=['id','value'])
	# ((2, u'FACULTY'), (3, u'AUTOMOTIVE MECHANIC'))
	# SELECT `id`, `value` FROM `jobs` WHERE `id` IN (2, 3) AND `sanitized` IS NULL

Inserting one record:
	
	db.insert(tablename='jobs', value={'value': 'MANAGER'})
	# INSERT INTO `jobs` (`value`) VALUES ('MANAGER')

Inserting multiple records:
	
	db.insertmany(tablename='jobs', 
	              field=['id', 'value'], 
	              value=[('5', 'TEACHER'), ('6', 'MANAGER')])
	# INSERT INTO `jobs` (`id`, `value`) VALUES (5, 'TEACHER'), (6, 'MANAGER')

Update a record:
	
	db.update(tablename='jobs', value={'value': 'MECHANIC'}, condition={'id': 3})
	# UPDATE `jobs` SET `value`='MECHANIC' WHERE id=3

Upserting a record. At least one primary key in _value_ is required, which would be used as condition when updating:
	
	db.update(tablename='jobs', value={'id': 3, 'value': 'MECHANIC'})
	# INSERT INTO `jobs` (`id`, `value`) VALUES (3, 'MECHANIC') ON DUPLICATE KEY UPDATE id=VALUES(id), value=VALUES(value)

Deleting a record:

	db.delete(tablename='jobs', 
	          condition={'value': ('FACULTY', 'MECHANIC'), 'sanitized': None})
	# DELETE FROM `jobs` WHERE `value` IN ('FACULTY', 'MECHANIC') AND `sanitized` IS NULL
