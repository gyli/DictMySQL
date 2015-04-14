#!/usr/bin/python
# -*-coding:UTF-8 -*-

import sys


_ver = sys.version_info

is_py2 = (_ver[0] == 2)

is_py3 = (_ver[0] == 3)

if is_py2:
    import MySQLdb
    import MySQLdb.cursors
elif is_py3:
    import pymysql as MySQLdb
    import pymysql.cursors


class DictMySQLdb:
    def __init__(self, host, user, passwd, db, port=3306, charset='utf8', init_command='SET NAMES UTF8',
                 dictcursor=False):
        self.host = host
        self.port = int(port)
        self.user = user
        self.passwd = passwd
        self.db = db
        self.dictcursor = dictcursor
        self.cursorclass = MySQLdb.cursors.DictCursor if dictcursor else MySQLdb.cursors.Cursor
        self.charset = charset
        self.init_command = init_command
        self.conn = MySQLdb.connect(host=self.host, port=self.port, user=self.user, passwd=self.passwd, db=self.db,
                                    charset=charset, init_command=init_command, cursorclass=self.cursorclass)
        self.cur = self.conn.cursor()

    def reconnect(self):
        try:
            self.cursorclass = MySQLdb.cursors.DictCursor if self.dictcursor else MySQLdb.cursors.Cursor
            self.conn = MySQLdb.connect(host=self.host, port=self.port, user=self.user, passwd=self.passwd,
                                        db=self.db, cursorclass=self.cursorclass, charset=self.charset,
                                        init_command=self.init_command)
            self.cur = self.conn.cursor()
            return True
        except MySQLdb.Error as e:
            print("Mysql Error: %s" % (e,))
            return False

    def query(self, sql, args=None):
        """
        :param sql: string. SQL query.
        :param args: tuple. Arguments of this query.
        """
        try:
            result = self.cur.execute(sql, args)
        except MySQLdb.Error as e:
            result = None
            print("Mysql Error: %s\nOriginal SQL:%s" % (e, sql))
        return result

    @staticmethod
    def _backtick(value):
        """
        :param value: str, list and dict are all accaptable.
        :return: string. Example: "`id`, `name`".
        """
        if isinstance(value, str):
            value = [value]
        elif isinstance(value, dict):
            value = value.keys()
        return ', '.join([''.join(['`', x, '`']) for x in value])

    @classmethod
    def _join_values(cls, value, placeholder='%s'):
        """
        Return "`id` = %s, `name` = %s". Only used in update(), no need to convert NULL values.
        :return: string
        """
        return ', '.join([' = '.join([cls._backtick(v), placeholder]) for v in value])

    @classmethod
    def _join_condition(cls, value, placeholder='%s'):
        """
        Return "`id` = %s AND `name` = %s" and it also converts None value into 'IS NULL' in sql.
        :return: string.
        """
        condition = []
        for v in value:
            if isinstance(value[v], (list, tuple, dict)):
                condition.append(cls._backtick(v) + ' IN (' + ', '.join([placeholder] * len(value[v])) + ')')
            elif value[v] is None:
                condition.append(cls._backtick(v) + ' IS NULL')
            else:
                condition.append(cls._backtick(v) + ' = ' + placeholder)
        return ' AND '.join(condition)

    @staticmethod
    def _condition_filter(condition):
        """
        Filter the None values and convert iterable items to elements in the original list.
        :return: list.
        """
        result = []
        for v in condition:
            if isinstance(condition[v], (list, tuple, dict)):
                for item in condition[v]:
                    result.append(item)
            # filter the None values since they would not be used as arguments
            elif condition[v] is not None:
                result.append(condition[v])
        return result

    def insert(self, tablename, value, ignore=False, commit=True):
        """
        Insert a dict into db.
        :return: int. The row id of the insert.
        """
        if not isinstance(value, dict):
            raise TypeError('Input value should be a dictionary')

        _sql = ''.join(['INSERT', ' IGNORE' if ignore else '', ' INTO ', self._backtick(tablename),
                        ' (', self._backtick(value), ') VALUES (', ', '.join(['%s'] * len(value)), ')'])

        self.cur.execute(_sql, list(value.values()))
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def insertmany(self, tablename, field, value, ignore=False, commit=True):
        """
        Insert multiple records within one query.
        Example: db.insertmany(tablename='jobs', field=['id', 'value'], value=[('5', 'TEACHER'), ('6', 'MANAGER')]).
        :param value: list. Example: [(value_1, value_2,), ].
        :return: int. The row id of the LAST insert only.
        """
        if not isinstance(value, (list, tuple)):
            raise TypeError('Input value should be a list or tuple')

        _sql = ''.join(['INSERT', ' IGNORE' if ignore else '', ' INTO ', tablename,
                        ' (', ', '.join(field), ') VALUES (', ', '.join(['%s'] * len(field)) + ')'])
        self.cur.executemany(_sql, value)
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def upsert(self, tablename, value, commit=True):
        """
        Example: db.update(tablename='jobs', value={'id': 3, 'value': 'MECHANIC'}).
        """
        if not isinstance(value, dict):
            raise TypeError('Input value should be a dictionary')

        _sql = ''.join(['INSERT INTO ', self._backtick(tablename), ' (', self._backtick(value), ') VALUES ',
                        '(', ', '.join(['%s'] * len(value)), ') ',
                        'ON DUPLICATE KEY UPDATE ', ', '.join([k + '=VALUES(' + k + ')' for k in value.keys()])])
        self.cur.execute(_sql, list(value.values()))
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def select(self, tablename, condition=None, field=None, insert=False, limit=0):
        """
        Example: db.select(tablename='jobs', condition={'id': (2, 3), 'sanitized': None}, field=['id','value'])
        :param condition: The conditions of this query in a dict. value=None means no condition and returns everything.
        :param field: Put the fields you want to select in a list, the default is id.
        :param insert: If insert==True, insert the input condition if there's no result and return the id of new row.
        :param limit: int. The max row number you want to get from the query. Default is 0 which means no limit.
        """
        # field is required
        if not field:
            raise ValueError('Argument field should not be empty.')

        # condition must be a dict
        if not isinstance(condition, dict):
            raise TypeError('Input value should be a dictionary')

        _sql = ''.join(['SELECT ', self._backtick(field),
                        ' FROM ', self._backtick(tablename),
                        ''.join([' WHERE ', self._join_condition(condition)]) if condition else '',
                        ''.join([' LIMIT ', str(limit)]) if limit else ''])

        if not condition:
            self.cur.execute(_sql)  # If condition is None, select all rows
        else:
            self.cur.execute(_sql, self._condition_filter(condition))
        ids = self.cur.fetchall()
        return ids if ids else (self.insert(tablename=tablename, value=condition) if insert else None)

    def get(self, tablename, condition, field='id', insert=True, ifnone=None):
        """
        A simplified method of select, for getting the first result in one field only. A common case of using this
        method is getting id.
        Example: db.get(tablename='jobs', condition={'id': 2}, field='value').
        :param insert: If insert==True, insert the input condition if there's no result and return the id of new row.
        :param ifnone: When ifnone is a non-empty string, raise an error if query returns empty result. insert parameter
                       would not work in this mode.
        """
        _sql = ''.join(['SELECT ', self._backtick(field), ' FROM ', self._backtick(tablename),
                        ' WHERE ', self._join_condition(condition), ' LIMIT 1'])
        result = self._condition_filter(condition)
        self.cur.execute(_sql, result)
        ids = self.cur.fetchone()
        _index = 0 if self.cursorclass is MySQLdb.cursors.Cursor else field
        if ids:
            return ids[_index]
        else:
            if ifnone:
                raise ValueError(ifnone)
            else:
                return self.insert(tablename=tablename, value=condition) if insert else None

    def update(self, tablename, value, condition, commit=True):
        """
        Example: db.update(tablename='jobs', value={'id': 3, 'value': 'MECHANIC'}).
        """
        _sql = ''.join(['UPDATE ', self._backtick(tablename), ' SET ', self._join_values(value),
                        ' WHERE ', self._join_condition(condition)])
        result = self._condition_filter(condition)
        self.cur.execute(_sql, (list(value.values()) + result))
        if commit:
            self.commit()

    def delete(self, tablename, condition):
        """
        Example: db.delete(tablename='jobs', condition={'value': ('FACULTY', 'MECHANIC'), 'sanitized': None}).
        """
        _sql = ''.join(['DELETE FROM ', self._backtick(tablename), ' WHERE ', self._join_condition(condition)])
        result = self._condition_filter(condition)
        return self.cur.execute(_sql, result)

    def now(self):
        self.cur.execute('SELECT NOW() as now;')
        return self.cur.fetchone()[0 if self.cursorclass is MySQLdb.cursors.Cursor else 'now'].strftime("%Y-%m-%d %H:%M:%S")

    def fetchone(self):
        result = self.cur.fetchone()
        return result

    def fetchall(self):
        result = self.cur.fetchall()
        return result

    def lastrowid(self):
        return self.cur.lastrowid

    def rowcount(self):
        return self.cur.rowcount

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def __del__(self):
        try:
            self.cur.close()
            self.conn.close()
        except:
            pass

    def close(self):
        self.cur.close()
        self.conn.close()