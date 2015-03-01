#!/usr/bin/python
# -*-coding:UTF-8 -*-

import MySQLdb
# import chardet


class DB:
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

    # Still using self.cur.execute due to eascape reason
    def sql(self, sql, args=None):
        try:
            n = self.cur.execute(sql, args)
            return n
        except MySQLdb.Error as e:
            print("Mysql Error:%s\nOriginal SQL:%s" % (e, sql))

    @staticmethod
    def _backtick(value, join=True):
        """
        :param join: If join is True, return a string "`id`, `name`"; otherwise, return a list ['`id`', '`name`']
        """
        if type(value) == str:
            value = [value]
        elif type(value) == dict:
            value = value.keys()
        result = [''.join(['`', x, '`']) for x in value]
        return ', '.join(result) if join else result

    @classmethod
    def _join_condition(cls, value, comma=False, placeholder='%s'):
        """
        :param comma: If comma is True, return "`id`=%s, `name`=%s"; otherwise, return "`id`=%s AND `name`=%s".
                      When comma is False, it can be used in conditions and converts None value into 'IS NULL' in sql.
                      Remember to filter the None when using value in execute()
        """
        return ', '.join([' = '.join([cls._backtick(v), placeholder]) for v in value]) if comma else \
            ' AND '.join([(cls._backtick(v) + ' IS NULL' if value[v] is None else ' = '.join([cls._backtick(v), placeholder])) for v in value])

    def insert(self, tablename, value, ignore=False, commit=True):
        """
        Insert a dict into db
        """
        if type(value) is not dict:
            raise TypeError('Input value should be a dictionary')

        # for v in value:
        #     value[v] = unicode(value[v], chardet.detect(value[v])['encoding']) if isinstance(value[v], str) else value[v]

        _sql = ''.join(['INSERT', ' IGNORE' if ignore else '', ' INTO ', self._backtick(tablename),
                        ' (', self._backtick(value), ') VALUES (', ', '.join(['%s'] * len(value)), ')'])

        self.cur.execute(_sql, value.values())
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def upsert(self, tablename, value, commit=True):
        if type(value) is not dict:
            raise TypeError('Input value should be a dictionary')

        _sql = ''.join(['INSERT INTO ', self._backtick(tablename), ' (', self._backtick(value), ') VALUES ',
                        '(', ', '.join(['%s'] * len(value)), ') ',
                        'ON DUPLICATE KEY UPDATE ', ', '.join([k+'=VALUES(' + k + ')' for k in value.keys()])])
        self.cur.execute(_sql, value.values())
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def select(self, tablename, value=None, field=None, insert=False, limit=0, multi=True):
        """
        :param value: The conditions of this query in a dict. value=None means no condition and returns everything.
        :param field: Put the fields you want to select in a list, the default is id
        :param insert: If insert==True, insert the input condition if there's no result and return the id of new row
        :param limit: The max row number you want to get from the query. Default is 0 which means no limit
        :param multi: If multi==False, return the value in first field of first row, otherwise, return all fields
                      in a tuple.
        """
        if field is None:
            field = ['id']

        if value is not None:
            if type(value) is not dict:
                raise TypeError('Input value should be a dictionary')

            if all(v is None for v in value.values()):
                return None

        _sql = ''.join(['SELECT ', self._backtick(field), ' FROM ', self._backtick(tablename),
                        '' if value is None else ''.join([' WHERE ', self._join_condition(value)]),
                        '' if limit == 0 else ''.join([' LIMIT ', str(limit)])])
        if value is None:
            self.cur.execute(_sql)
        else:
            self.cur.execute(_sql, filter(None, value.values()))
        ids = self.cur.fetchall()
        return (self.insert(tablename=tablename, value=value) if insert else None) if ids == () else (
            tuple(i for i in (ids[0] if limit else ids)) if multi else ids[0][0])

    def get(self, tablename, value, field='id', insert=True, ifnone=None):
        """
        A simplified method of select, for getting the first result from one field only
        :param ifnone: When ifnone is a non-empty string, raise an error if query return empty result. insert parameter
                       won't work in this mode.
        """
        if all(v is None for v in value.values()):
            return None

        _sql = ''.join(['SELECT ', self._backtick(field), ' FROM ', self._backtick(tablename),
                        ' WHERE ', self._join_condition(value), ' LIMIT 1'])

        self.cur.execute(_sql, filter(None, value.values()))
        ids = self.cur.fetchone()
        if ifnone is None:
            return (self.insert(tablename=tablename, value=value) if insert else None) if ids is None else ids[0]
        else:
            if ids is None:
                raise ValueError(ifnone)
            else:
                return ids[0]

    def update(self, tablename, condition, value, commit=True):
        _sql = ''.join(['UPDATE ', self._backtick(tablename), ' SET ', self._join_condition(value, comma=True),
                        ' WHERE ', self._join_condition(condition)])
        self.cur.execute(_sql, (value.values() + filter(None, condition.values())))
        if commit:
            self.commit()

    def delete(self, tablename, condition):
        _sql = ''.join(['DELETE FROM ', self._backtick(tablename), ' WHERE ', self._join_condition(condition)])
        return self.cur.execute(_sql, filter(None, condition.values()))

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