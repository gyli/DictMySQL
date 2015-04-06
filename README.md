# DictMySQLdb
A mysql package above MySQL-python for more convenient database manipulation with Python dictionary.

Unlike DictCursor in MySQLdb, DictMySQLdb allows passing values and conditions as dictionary to MySQL.

Besides of the methods MySQL-python offers, MySQLTool provides the following methods:

* `insert()`
* `insertmany()`
* `upsert()`
* `get()`
* `update()`
* `select()`
* `delete()`
* `now()`

## Example

Create connection:

	db = DictMySQLdb(db='occupation', host='127.0.0.1', passwd='', user='root')
	
Fetch one record:

	db.get(tablename='raw_occupations', condition={'id': 2}, field='value')
	# u'FACULTY'

Pass multiple conditions:

	db.select(tablename='raw_occupations', condition={'id': (2, 3), 'sanitized': 'no'}, field=['id','value'])
	# ((2, u'FACULTY'), (3, u'AUTOMOTIVE MECHANIC'))

Insert one record:
	
	db.insert(tablename='raw_occupations', value={'value': 'MANAGER'})

Insert multiple records:
	
	db.insertmany(tablename='raw_occupations', field=['id', 'value'], value=(['5', 'TEACHER'], ['6', 'MANAGER']))

Upsert a record with a primary key in _value_:
	
	db.update(tablename='raw_occupations', value={'id': 3, 'value': 'MECHANIC'})

Delete a record:

	db.delete(tablename='raw_occupations', condition={'value': ('FACULTY', 'MECHANIC'), 'sanitized': 'no'})
	