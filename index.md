---
layout: page
title: DictMySQL
description: More convenient database manipulation with Python dictionary.
---

## Installation
```bash
pip install dictmysql
```

## Initialization of DictMySQL()

#### Parameters:
- **host**: _string_   
- **user**: _string_   
- **passwd**: _string_  
- **db**: _string_  
- **port**: _int, default 3306_  
- **charset**: _string, default 'utf8'_  
- **init_command**: _string, default 'SET NAMES UTF8'_  
- **dictcursor**: _bool, default False_  
When it is True, the connector uses DictCursor instead of regular cursor, so that all the return of SQL query will be wrapped in dict.   
- **use_unicode**: _bool, default True_  

#### Returns: 
DictMySQL object

#### Example:
```python
from dictmysql import DictMySQL
mysql = DictMySQL(db='occupation', 
                  host='127.0.0.1', 
                  user='root', 
                  passwd='')
```

***





## select()

#### Parameters:
- **table**: _string_   
- **columns**: _list, default None_  
By default, it selects all columns.
- **join**: _dict, default None_   
See [JOIN Syntax](#join-syntax) for more details.
- **where**: _dict, default None_   
See [WHERE Syntax](#where-syntax) for more details.
- **group**: _string\|list, default None_
- **having**: _string, default None_
- **order**: _string\|list, default None_   
- **limit**: _int\|list, default None_   
- **iterator**: _bool, default False_
Whether to output the result in a generator
- **fetch**: _bool, default True_
Whether to fetch the result. When False, it returns number of lines in result.

#### Returns: 
The result of SQL query.

#### Examples:
```python
mysql.select(table='jobs', 
             where={'value': 'Artist'})
# SELECT * FROM `jobs` WHERE (`value` = "Artist");
# Output: (5, )

mysql.select(table='jobs', 
             where={'value': None})
# SELECT * FROM `jobs` WHERE (`value` IS NULL);

mysql.select(table='jobs', 
             where={'jobs.value': 'Artist'},
             order='id DESC',
             limit=[2, 10])
# SELECT * FROM `jobs` WHERE (`jobs`.`value` LIKE "Artist") ORDER BY id DESC LIMIT 2, 10;
# Parameter limit not only accept int, but also list value if there is offset.
```

#### SQL Functions
For all SQL functions, add a `#` before the column name or function name, and the value will not be quoted or escaped.

```python
mysql.select(table='jobs', columns=['#min(id)', 'value'], where={'value': {'$LIKE': 'Art%'}})
# SELECT min(id), `value` FROM `profile_job` WHERE (`value` LIKE Art%);
```
***





## get()
A simplified method of select(), for getting one result in a single column. It can insert the condition as a new record when there is no result found. The result will not be wrapped in a tuple or dict, no matter which cursor is being used. A common case of using this method is fetching the unique id with given condition.

It only outputs the first select query under debug mode, since it does not execute the query.

#### Parameters:
- **table**: _string_   
- **column**: _string_  
- **join**: _dict, default None_   
See [JOIN Syntax](#join-syntax) for more details.
- **where**: _dict, default None_   
See [WHERE Syntax](#where-syntax) for more details.
- **insert**: _bool, default False_   
When it is True, insert the input condition if there is no result found and return the id of new row.
- **ifnone**: _string, default None_   
When it is not null, raise an error with the input string if there is no result found. Parameter insert will be unavailable in this situation.

#### Returns: 
The single result of SQL query.

#### Examples:
```python
mysql.get(table='jobs', 
          column='id', 
          where={'value': 'Artist'})
# SELECT `id` FROM `jobs` WHERE (`value` = "Artist") LIMIT 1;
# Output: 5
```

***






## insert()

#### Parameters:
- **table**: _string_   
- **value**: _dict_  
- **ignore**: _bool, default False_   
Add the IGNORE option into the insert statement.
- **commit**: _bool, default True_   
Whether to commit the statement.

#### Returns: 
The last inserted id.

#### Examples:
```python
mysql.insert(table='jobs', 
             value={'value': 'Programmer'})
# INSERT INTO `jobs` (`value`) VALUES ("Programmer");
```

#### SQL Functions
For all SQL functions, add a `#` before the column name and its value will not be quoted or escaped.

```python
mysql.insert(table='jobs', 
             value={'#UID': 'UUID()', 'value': 'Programmer'})
# INSERT INTO `jobs` (`UID`, `value`) VALUES (UUID(), "Programmer");
```
***





## insertmany()
Insert multiple values in one statement. SQL function is not supported in this method.

#### Parameters:
- **table**: _string_   
- **columns**: _list_   
Column names need to be specified when inserting multiple values.
- **value**: _list\|tuple_  
- **ignore**: _bool, default False_   
Add the IGNORE option into the insert statement.
- **commit**: _bool, default True_   
Whether to commit the statement.

#### Returns: 
The last inserted id.

#### Examples:
```python
mysql.insertmany(table='jobs', 
                 columns=['value', 'available'], 
                 value=(('Programmer', 'yes'), ('Manager', 'no'))
# INSERT INTO `jobs` (`value`) VALUES ("Programmer", "yes"), ("Manager", "no");
```
***




## upsert()
Update or insert the values with "ON DUPLICATE KEY UPDATE" syntax. Unique index is required for at least one of the columns.

#### Parameters:
- **table**: _string_   
- **value**: _dict_  
- **update_columns**: _list, default None_   
Specify the columns which will be updated if record exists. If it is None, all the columns in value will be update if possible.
- **commit**: _bool, default True_   
Whether to commit the statement.

#### Returns: 
The last inserted id.

#### Examples:
```python
mysql.upsert(table='jobs', 
             value={'id': 5, 'value': 'Artist'})
# INSERT INTO `jobs` (`id`, `value`) VALUES (5, Artist) ON DUPLICATE KEY UPDATE `id`=VALUES(`id`), `value`=VALUES(`value`);
```
***





## update()

#### Parameters:
- **table**: _string_   
- **value**: _dict_  
- **where**: _dict, default None_   
See [WHERE Syntax](#where-syntax) for more details.
- **commit**: _bool, default True_   
Whether to commit the statement.

#### Returns: 
The number of effected rows.

#### Examples:
```python
mysql.update(table='jobs', 
             value={'value': 'Artist'},
             where={'id': 3})
# UPDATE `jobs` SET `value` = "Artist" WHERE (`id` = 3);

# Similar to SQL functions, add `#` when setting a column equal to another column:
mysql.update(table='jobs(j)',
             join={'profile_job(pj)': {'pj.job_id': 'j.id'}},
             value={'#j.value': 'pj.job_value'},
             where={'j.id': 3})
# UPDATE `jobs` AS `j` JOIN `profile_job` AS `pj` ON `pj`.`job_id`=`j`.`id` SET `j`.`value` = pj.job_value WHERE (`j`.`id` = 3);"

```
***






## delete()

#### Parameters:
- **table**: _string_   
- **where**: _dict, default None_   
See [WHERE Syntax](#where-syntax) for more details.
- **commit**: _bool, default True_   
Whether to commit the statement.

#### Returns: 
The number of effected rows.

#### Examples:
```python
mysql.delete(table='jobs', where={'id': 3})
# DELETE FROM `jobs` WHERE (`id` = 3);



mysql.delete(table='jobs', where={'id': 3}, commit=False)
# Do something else
mysql.commit()
# Commit all statements above
```
***






## query()
Run customized SQL query. Just like PyMySQL and MySQLdb, use fetchall() or fetchone() method to fetch the results.

#### Parameters:
- **sql**: _string_   
- **args**: _tuple\|list, default None_

#### Examples:
```python
mysql.query("SELECT * from jobs where value = %s", ('manager',))
result = mysql.fetchall()
print(result)
# Output: ((10, "Manager"),)
```
***






## now()
```python
mysql.now()
# SELECT NOW() AS now;
```
***






## last_insert_id()
Fetching the id of last inserted row.

```python
mysql.last_insert_id()
# SELECT LAST_INSERT_ID() AS lid;;
```
***






## WHERE Syntax
DictMySQL provides a powerful WHERE syntax parser, transforming conditions from dict into SQL query.

#### Simple Examples:
```python
where = {'id': 5, 'value': 'Artist'}
# WHERE (`id` = 5) AND (`value` = "Artist")
# The default operator is "=".

where = {
    '$>=': {
        'id': 5
    },
    '$LIKE': {
        'value': 'Art%'
    }
}
# WHERE (`id` >= 5) AND (`value` LIKE "Art%")
# The default logic operator is "AND".


where = {
    '$OR': [
        {
            'id':
                [
                    5, 10
                ]
        },
        {
            '$IN': {
                'value': [
                    'Programmer', 'Manager'
                ]
            }
        }
    ]
}
# WHERE ((`id` IN (5, 10)) OR (`value` IN ("Programmer", "Manager")));
# The default operator is "IN" if the end value is a list.
```
List of operators:

- **$=** or **$EQ**
- **$<** or **$LT**
- **$<=** or **$LTE**
- **$>** or **$GT**
- **$>=** or **$GTE**
- **$<>** or **$NE**
- **$LIKE**
- **$BETWEEN**
- **$IN**

Operators are case-insensitive.

#### Some Quick Examples:
```python
where = {
    'id': {
        '$BETWEEN': [
            5, 10
        ]
    }
}
# WHERE (`id` BETWEEN 5 AND 10)
# Between operator only takes the first two values to build the statement.


where = {
    '$AND': [
        {
            '$>': {
                'id': 5
            }
        },
        {
            'id': {
                '$<': 10
            }
        }
    ]
}
# WHERE ((`id` > 5) AND (`id` < 10))
# Switching the position of operator and column name is also acceptable.
```

#### $NOT operator
```python
where = {
    '$NOT': {
        '$AND': [
            {
                '$>': {
                    'id': 5
                }
            },
            {
                'id': {
                    '$<': 10
                }
            }
        ]
    }
}
# WHERE ((`id` <= 5) OR (`id` >= 10))
# A $NOT operator will reverse the meaning of whole operator chain. 
# In the example above, $AND -> $OR and $< -> $>=.
```

#### Some More Complex Examples:
```python
# Note that switching the position of $NOT and other operators might cause ambiguity. 
# It might reverse the whole operator chain or the single operator only, which will 
# be confusing since it can't be distinguished from the input JSON. So we define：
# Reverse the logic operator, if $NOT is parent node and the related operator is child node.
# Example, (not (A and B)): 
where = {
    '$NOT': {
        '$AND': [
            {
                '$LIKE': {
                    'name': 'David%'
                }
            },
            {
                '$LIKE': {
                    'name': '%Lee'
                }
            }
        ]
    }
}
# (`name` NOT LIKE 'David%') OR (`name` NOT LIKE '%Lee')


# Keep the logic operator, if $NOT is child node and operator is parent node.
# Example, ((not A) and (not B)): 
where = {
    'name': {
        '$AND': [
            {
                '$NOT': {
                    '$LIKE': 'David%'
                }
            },
            {
                '$NOT': {
                    '$LIKE': '%Lee'
                }
            }
        ]
    }
}
# (`name` NOT LIKE 'David%') AND (`name` NOT LIKE '%Lee')
```

#### Compound logic operator
```python
where = {
    '$AND': [
        {
            '$OR': [
                {
                    'id': 5
                }, 
                {
                    'id': 10
                }
            ]
        }, 
        {
            '$LIKE': {
                'value': 'Art%'
            }
        }
    ]
}
# WHERE (((`id` = 5) OR (`id` = 10)) AND (`value` LIKE "Art%"))
```

#### SQL Functions
For all SQL functions, add a `#` before the column name and its value will not be quoted or escaped.

```python
where = {
    '#created': {
        '$=': 'date(now())'
    }
}
# WHERE (`created` = date(now()))
```
***





## JOIN Syntax
DictMySQL provides simple symbolic syntax for joining tables.

List of join types:

- **>**: LEFT JOIN
- **<**: RIGHT JOIN
- **<>**: FULL JOIN
- **><**: INNER JOIN

#### Examples:

```python
mysql.select(table='jobs', 
             join={
                 '[>]profile_job': {
                     'jobs.id': 'profile_job.job_id'
                 }
             })
# SELECT * FROM `jobs` LEFT JOIN `profile_job` ON `jobs`.`id`=`profile_job`.`job_id`;

mysql.select(table='jobs', 
             join={
                 'profile_job': {
                     'jobs.id': 'profile_job.job_id'
                 }
             })
# SELECT * FROM `jobs` JOIN `profile_job` ON `jobs`.`id`=`profile_job`.`job_id`;
# INNER JOIN by default

mysql.select(table='jobs', 
             join={
                 'profile_job': {
                     'jobs.id': 'profile_job.job_id',
                     'jobs.id': {'$>': 'profile_job.job_id'}
                 },
                 'company': {
                     'jobs.id': 'company.job_id',
                 }
             })
# SELECT * FROM `jobs` JOIN `profile_job` ON `jobs`.`id`=`profile_job`.`job_id` AND `jobs`.`id`>`profile_job`.`job_id` JOIN `company` ON `jobs`.`id`=`company`.`job_id`;
# Similar to WHERE, the operator in JOIN could be <, <=, >, >=, <> and =.
# Tables could be joined on multiple conditions with AND.
```

#### Alias
Both of the parameter table and join support alias.

```python
mysql.select(table='jobs(j)',
             columns=['j.value', 'p.value'],
             join={
                 '[<>]profile_job(pj)': {
                     'j.id': 'pj.job_id'
                 },
                 '[<>]profile(p)': {
                     'pj.profile_id': 'p.id'
                 }
             })
# SELECT `j`.`value`, `p`.`value` FROM `jobs` AS `j` FULL JOIN `profile` AS `p` ON `pj`.`profile_id`=`p`.`id` FULL JOIN `profile_job` AS `pj` ON `j`.`id`=`pj`.`job_id`;

# When performing self join, the joined table should be assigned different alias, 
# otherwise they will have the same key.
mysql.select(table='profile_job(pj)',
             join={
                 'profile_job(pj2)': {
                     'pj.id': 'pj1.id_2'
                 },
                 'profile_job(pj3)': {
                     'pj.id': 'pj2.id_3'
                 }
             })
# SELECT * FROM `profile_job` AS `pj` JOIN `profile_job` AS `pj2` ON `pj`.`id`=`pj2`.`id_2` JOIN `profile_job` AS `pj3` ON `pj`.`id`=`pj3`.`id_3`;
```
***

## Reconnect
DictMySQL provides reconnect method allowing user to reconnect to MySQL manually.

```python
mysql = DictMySQL(db='occupation', 
                  host='127.0.0.1', 
                  user='root', 
                  passwd='')
mysql.now()
# Wait a long time and MySQL server has gone away
mysql.reconnect()
mysql.now()
# Works again
```
***

## Debug
By setting `DictMySQL.debug = True`, all the query methods excluding query() will print the SQL query without running it. Under current version it will not print the quotation mark.

```python
mysql.debug = True
mysql.select(table='jobs', 
             where={'value': 'Artist'})
# Output: 'SELECT * FROM `jobs` WHERE (`value` = Artist);'
```
