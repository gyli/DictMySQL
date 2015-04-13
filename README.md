# DictMySQLdb
A mysql package on the top of MySQL-python for more convenient database manipulation with Python dictionary.

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

## Examples

Creating connection:

	db = DictMySQLdb(db='occupation', host='127.0.0.1', passwd='', user='root')
	
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

Upserting a record with a primary key in _value_:
	
	db.update(tablename='jobs', value={'id': 3, 'value': 'MECHANIC'})
	# INSERT INTO `jobs` (`id`, `value`) VALUES (3, 'MECHANIC') ON DUPLICATE KEY UPDATE id=VALUES(id), value=VALUES(value)

Deleting a record:

	db.delete(tablename='jobs', 
	          condition={'value': ('FACULTY', 'MECHANIC'), 'sanitized': None})
	# DELETE FROM `jobs` WHERE `value` IN ('FACULTY', 'MECHANIC') AND `sanitized` IS NULL
