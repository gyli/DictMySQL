#!/usr/bin/python
# -*-coding:UTF-8 -*-

import MySQLdb
# import chardet


class DictMySQLdb:
    def __init__(self, host, user, passwd, db, port=3306, charset='utf8', init_command='SET NAMES UTF8'):
        self.host = host
        self.port = int(port)
        self.user = user
        self.passwd = passwd
        self.db = db
        self.charset = charset
        self.init_command = init_command
        self.conn = MySQLdb.connect(host=self.host, port=self.port, user=self.user, passwd=self.passwd, db=db,
                                    charset=charset, init_command=init_command)
        self.cur = self.conn.cursor()

    def reconnect(self):
        try:
            self.conn = MySQLdb.connect(host=self.host, port=self.port, user=self.user, passwd=self.passwd, db=self.db,
                                        charset=self.charset, init_command=self.init_command)
            return True
        except Exception:
            return False

    def sql(self, sql, args=None):
        try:
            n = self.cur.execute(sql, args)
            return n
        except MySQLdb.Error as e:
            print("Mysql Error:%s\nOriginal SQL:%s" % (e, sql))

    @staticmethod
    def _backtick(value, join=True):
        """
        :param value: str, list and dict are all accaptable.
        :param join: If join is True, return a string "`id`, `name`"; otherwise, return a list ['`id`', '`name`']
        :return: string
        """
        if type(value) == str:
            value = [value]
        elif type(value) == dict:
            value = value.keys()
        result = [''.join(['`', x, '`']) for x in value]
        return ', '.join(result) if join else result

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
        :return: string
        """
        condition = []
        for v in value:
            if hasattr(value[v], '__iter__'):
                condition.append(cls._backtick(v) + ' IN (' + ', '.join([placeholder] * len(value[v])) + ')')
            elif value[v] is None:
                condition.append(cls._backtick(v) + ' IS NULL')
            else:
                condition.append(cls._backtick(v) + ' = ' + placeholder)
        return ' AND '.join(condition)

    @staticmethod
    def _condition_filter(condition):
        """
        Filter the None values and convert iterable items to elements in the original list
        :return: list
        """
        result = []
        for v in condition:
            if hasattr(condition[v], '__iter__'):
                for item in condition[v]:
                    result.append(item)
            # still allow 0
            elif condition[v] is not None:
                result.append(condition[v])
        return result

    def insert(self, tablename, value, ignore=False, commit=True):
        """
        Insert a dict into db
        """
        if type(value) is not dict:
            raise TypeError('Input value should be a dictionary')

        # TODO: unicode for input value
        # for v in value:
        # value[v] = unicode(value[v], chardet.detect(value[v])['encoding']) if isinstance(value[v], str) else value[v]

        _sql = ''.join(['INSERT', ' IGNORE' if ignore else '', ' INTO ', self._backtick(tablename),
                        ' (', self._backtick(value), ') VALUES (', ', '.join(['%s'] * len(value)), ')'])

        self.cur.execute(_sql, value.values())
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def insertmany(self, tablename, field, value, ignore=False, commit=True):
        """
        Insert multiple records within one query.
        Example: db.insertmany(tablename='jobs', field=['id', 'value'], value=(['5', 'TEACHER'], ['6', 'MANAGER']))
        :param value: list [(value_1, value_2,), ]
        """
        if type(value) is not list:
            raise TypeError('Input value should be a list')

        _sql = ''.join(['INSERT', ' IGNORE' if ignore else '', ' INTO ', tablename,
                        ' (', ', '.join(field), ') VALUES (', ', '.join(['%s'] * len(field)) + ')'])
        self.cur.executemany(_sql, value)
        if commit:
            self.conn.commit()

    def upsert(self, tablename, value, commit=True):
        """
        Example: db.update(tablename='jobs', value={'id': 3, 'value': 'MECHANIC'})
        """
        if type(value) is not dict:
            raise TypeError('Input value should be a dictionary')

        _sql = ''.join(['INSERT INTO ', self._backtick(tablename), ' (', self._backtick(value), ') VALUES ',
                        '(', ', '.join(['%s'] * len(value)), ') ',
                        'ON DUPLICATE KEY UPDATE ', ', '.join([k + '=VALUES(' + k + ')' for k in value.keys()])])
        self.cur.execute(_sql, value.values())
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def select(self, tablename, condition=None, field=None, insert=False, limit=0, multi=True):
        """
        Example: db.select(tablename='jobs', condition={'id': (2, 3), 'sanitized': None}, field=['id','value'])
        :param condition: The conditions of this query in a dict. value=None means no condition and returns everything.
        :param field: Put the fields you want to select in a list, the default is id
        :param insert: If insert==True, insert the input condition if there's no result and return the id of new row
        :param limit: The max row number you want to get from the query. Default is 0 which means no limit
        :param multi: If multi==False, return the value in first field of first row, otherwise, return all fields
                      in a tuple.
        """
        if field is None:
            field = ['id']

        if condition is not None:
            if type(condition) is not dict:
                raise TypeError('Input value should be a dictionary')

            if all(v is None for v in condition.values()):
                return None

        _sql = ''.join(['SELECT ', self._backtick(field), ' FROM ', self._backtick(tablename),
                        '' if condition is None else ''.join([' WHERE ', self._join_condition(condition)]),
                        '' if limit == 0 else ''.join([' LIMIT ', str(limit)])])
        if condition is None:
            self.cur.execute(_sql)
        else:
            result = self._condition_filter(condition)
            self.cur.execute(_sql, result)
        ids = self.cur.fetchall()
        return (self.insert(tablename=tablename, value=condition) if insert else None) if ids == () else (
            tuple(i for i in (ids[0] if limit else ids)) if multi else ids[0][0])

    def get(self, tablename, condition, field='id', insert=True, ifnone=None):
        """
        A simplified method of select, for getting the first result in one field only. A common case of using this
        method is getting id.
        Example: db.get(tablename='jobs', condition={'id': 2}, field='value')
        :param insert: If insert==True, insert the input condition if there's no result and return the id of new row
        :param ifnone: When ifnone is a non-empty string, raise an error if query returns empty result. insert parameter
                       would not work in this mode.
        """
        if all(v is None for v in condition.values()):
            return None

        _sql = ''.join(['SELECT ', self._backtick(field), ' FROM ', self._backtick(tablename),
                        ' WHERE ', self._join_condition(condition), ' LIMIT 1'])

        result = self._condition_filter(condition)
        self.cur.execute(_sql, result)
        ids = self.cur.fetchone()
        if ifnone is None:
            return (self.insert(tablename=tablename, value=condition) if insert else None) if ids is None else ids[0]
        else:
            if ids is None:
                raise ValueError(ifnone)
            else:
                return ids[0]

    def update(self, tablename, value, condition, commit=True):
        """
        Example: db.update(tablename='jobs', value={'id': 3, 'value': 'MECHANIC'})
        """
        _sql = ''.join(['UPDATE ', self._backtick(tablename), ' SET ', self._join_values(value),
                        ' WHERE ', self._join_condition(condition)])
        result = self._condition_filter(condition)
        self.cur.execute(_sql, (value.values() + result))
        if commit:
            self.commit()

    def delete(self, tablename, condition):
        """
        Example: db.delete(tablename='jobs', condition={'value': ('FACULTY', 'MECHANIC'), 'sanitized': None})
        """
        _sql = ''.join(['DELETE FROM ', self._backtick(tablename), ' WHERE ', self._join_condition(condition)])
        result = self._condition_filter(condition)
        return self.cur.execute(_sql, result)

    def now(self):
        self.cur.execute('SELECT NOW();')
        return self.cur.fetchone()[0].strftime("%Y-%m-%d %H:%M:%S")

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

    def close(self):
        self.cur.close()
        self.conn.close()