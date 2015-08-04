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
                 dictcursor=False, use_unicode=True):
        self.host = host
        self.port = int(port)
        self.user = user
        self.passwd = passwd
        self.db = db
        self.dictcursor = dictcursor
        self.cursorclass = MySQLdb.cursors.DictCursor if dictcursor else MySQLdb.cursors.Cursor
        self.charset = charset
        self.init_command = init_command
        self.use_unicode = use_unicode
        self.conn = MySQLdb.connect(host=self.host, port=self.port, user=self.user, passwd=self.passwd, db=self.db,
                                    charset=charset, init_command=init_command, cursorclass=self.cursorclass, use_unicode=self.use_unicode)
        self.cur = self.conn.cursor()

    def reconnect(self):
        try:
            self.cursorclass = MySQLdb.cursors.DictCursor if self.dictcursor else MySQLdb.cursors.Cursor
            self.conn = MySQLdb.connect(host=self.host, port=self.port, user=self.user, passwd=self.passwd,
                                        db=self.db, cursorclass=self.cursorclass, charset=self.charset,
                                        init_command=self.init_command,
                                        use_unicode=self.use_unicode)
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
        :type value: str|list|dict
        :return: string. Example: "`id`, `name`".
        """
        if isinstance(value, (str, unicode)):
            value = [value]
        # If there's a dot, only append the backticks to the first part
        return ', '.join(['.'.join(['`' + v.split('.')[0] + '`'] + v.split('.')[1:]) for v in value])

    def _concat_values(self, value, placeholder='%s'):
        """
        Return "`id` = %s, `name` = %s". Only used in update(), no need to convert NULL values.
        """
        return ', '.join([' = '.join([self._backtick(v), placeholder]) for v in value])

    def _condition_parser(self, value, placeholder='%s'):
        """
        Accept: {'id': 5, 'name': None}
        Return: "`id` = %s AND `name` IS NULL"
        """
        condition = []
        for v in value:
            if isinstance(value[v], (list, tuple, dict)):
                _cond = ' IN (' + ', '.join([placeholder] * len(value[v])) + ')'
            elif value[v] is None:
                _cond = ' IS NULL'
            else:
                _cond = ' = ' + placeholder
            condition.append(self._backtick(v) + _cond)
        return ' AND '.join(condition)

    def _where_parser(self, where, placeholder='%s'):
        result = {'q': [], 'v': ()}

        _operators = {
            '$=': '=',
            '$EQ': '=',
            '$<': '<',
            '$LT': '<',
            '$>': '>',
            '$GT': '>',
            '$<=': '<=',
            '$LTE': '<=',
            '$>=': '>=',
            '$GTE': '>=',
            '$<>': '<>',
            '$NE': '<>',
            '$IS': 'IS',
            '$LIKE': 'LIKE',
            '$BETWEEN': 'BETWEEN',
            '$IN': 'IN',
            '$NIN': 'NOT IN'
        }

        _connectors = {
            '$AND': 'AND',
            '$OR': 'OR'
        }

        result = {'q': [], 'v': ()}
        placeholder = '%s'

        def _combining(_cond, _operator=None, upper_key=None, connector=None):
            # {'OR': [{'zipcode': {'<': '22}}]}
            if isinstance(_cond, dict):
                i = 1
                for k, v in _cond.iteritems():
                    if k.upper() in _connectors:
                        result['q'].append('(')
                        _combining(v, upper_key=upper_key, _operator=_operator, connector=_connectors[k.upper()])
                        result['q'].append(')')
                    # {'>':{'value':10}}
                    elif k.upper() in _operators:
                        _combining(v, _operator=_operators[k.upper()], upper_key=upper_key, connector=connector)
                    # {'value':10}
                    else:
                        _combining(v, upper_key=k, _operator=_operator, connector=connector)
                    # default 'AND' except for the last one
                    if i < len(_cond):
                        result['q'].append(' AND ')
                    i += 1
            elif isinstance(_cond, list):
                l_index = 1
                for l in _cond:
                    _combining(l, _operator=_operator, upper_key=upper_key, connector=connector)
                    if l_index < len(_cond):
                        result['q'].append(' ' + connector + ' ')
                    l_index += 1
            else:
                if _operator:
                    s_q = self._backtick(upper_key) + ' ' + _operator + ' ' + placeholder
                else:
                    s_q = self._backtick(upper_key) + ' = ' + placeholder
                result['q'].append('(' + s_q + ')')
                result['v'] += (_cond,)

        _combining(where)
        return [''.join(result['q']), result['v']]

    @staticmethod
    def _condition_filter(condition):
        """
        Filter the None values and convert iterable items to elements in the original list.
        """
        result = ()
        for v in condition:
            # filter the None values since they would not be used as arguments
            if isinstance(condition[v], (list, tuple, dict)):
                result += tuple(condition[v])
            elif condition[v] is not None:
                result += (condition[v],)
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
        _args = tuple(value.values())
        self.cur.execute(_sql, _args)
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def insertmany(self, tablename, field, value, ignore=False, commit=True):
        """
        Insert multiple records within one query.
        Example: db.insertmany(tablename='jobs', field=['id', 'value'], value=[('5', 'TEACHER'), ('6', 'MANAGER')]).
        :type value: list
        :param value: Example: [(value_1, value_2,), ].
        :return: int. The row id of the LAST insert only.
        """
        if not isinstance(value, (list, tuple)):
            raise TypeError('Input value should be a list or tuple')

        _sql = ''.join(['INSERT', ' IGNORE' if ignore else '', ' INTO ', tablename,
                        ' (', ', '.join(field), ') VALUES (', ', '.join(['%s'] * len(field)) + ')'])
        _args = tuple(value)
        self.cur.executemany(_sql, _args)
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def upsert(self, tablename, value, commit=True):
        """
        Example: db.upsert(tablename='jobs', value={'id': 3, 'value': 'MECHANIC'}).
        """
        if not isinstance(value, dict):
            raise TypeError('Input value should be a dictionary')

        _sql = ''.join(['INSERT INTO ', self._backtick(tablename), ' (', self._backtick(value), ') VALUES ',
                        '(', ', '.join(['%s'] * len(value)), ') ',
                        'ON DUPLICATE KEY UPDATE ', ', '.join([k + '=VALUES(' + k + ')' for k in value.keys()])])
        _args = tuple(value.values())
        self.cur.execute(_sql, _args)
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def select(self, tablename, field, join=None, condition=None, where=None, limit=0):
        """
        Example: db.select(tablename='jobs', condition={'id': (2, 3), 'sanitized': None}, field=['id','value'])
        :param condition: The conditions of this query in a dict. value=None means no condition and returns everything.
        :param field: Put the fields you want to select in a list.
        :type limit: int
        :param limit: The max row number you want to get from the query. Default is 0 which means no limit.
        """
        if not condition:
            condition = {}

        # Combine the arguments
        _args = self._condition_filter(condition)
        if where:
            where_q, where_v = self._where_parser(where)
            _args += where_v

        # Concat the AS if there is
        if isinstance(tablename, dict):
            tablename = self._backtick(tablename['table']) + (' AS ' + tablename['as'] + ' ' if tablename['as'] else '')
        else:
            tablename = self._backtick(tablename)

        # Format the key in join
        if join:
            join = [{k.lower(): v for k, v in j.iteritems()} for j in join]

        _sql = ''.join(['SELECT ', self._backtick(field),
                        ' FROM ', tablename,
                        ' '.join([' '.join([t.get('type', ''), 'JOIN', t['table']] +
                                           ['AS ' + t.get('as') if t.get('as') else ''] +
                                           ['ON', t['on']]) for t in join]) if join else '',
                        ' WHERE ' if condition or where else '',
                        self._condition_parser(condition) if condition else '',
                        ' AND ' if condition and where else '',
                        where_q if where else '',
                        ''.join([' LIMIT ', str(limit)]) if limit else ''])

        self.cur.execute(_sql, _args)
        ids = self.cur.fetchall()
        return ids if ids else None

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
                        ' WHERE ', self._condition_parser(condition), ' LIMIT 1'])
        _args = self._condition_filter(condition)
        self.cur.execute(_sql, _args)
        ids = self.cur.fetchone()
        if ids:
            return ids[0 if self.cursorclass is MySQLdb.cursors.Cursor else field]
        else:
            if ifnone:
                raise ValueError(ifnone)
            else:
                return self.insert(tablename=tablename, value=condition) if insert else None

    def update(self, tablename, value, condition, commit=True):
        """
        Example: db.update(tablename='jobs', value={'value': 'MECHANIC'}, condition={'id': 3}).
        """
        # TODO: join support
        _sql = ''.join(['UPDATE ', self._backtick(tablename), ' SET ', self._concat_values(value),
                        ' WHERE ', self._condition_parser(condition)])
        _args = tuple(value.values()) + self._condition_filter(condition)
        result = self.cur.execute(_sql, _args)
        if commit:
            self.commit()
        return result

    def delete(self, tablename, condition, commit=True):
        """
        Example: db.delete(tablename='jobs', condition={'value': ('FACULTY', 'MECHANIC'), 'sanitized': None}).
        """
        _sql = ''.join(['DELETE FROM ', self._backtick(tablename), ' WHERE ', self._condition_parser(condition)])
        _args = self._condition_filter(condition)
        result = self.cur.execute(_sql, _args)
        if commit:
            self.commit()
        return result

    # TODO: CREATE method

    def now(self):
        self.cur.execute('SELECT NOW() as now;')
        return self.cur.fetchone()[0 if self.cursorclass is MySQLdb.cursors.Cursor else 'now'].strftime("%Y-%m-%d %H:%M:%S")

    def last_insert_id(self):
        self.query("SELECT LAST_INSERT_ID() AS lid")
        return self.cur.fetchone()[0 if self.cursorclass is MySQLdb.cursors.Cursor else 'lid']

    def fetchone(self):
        return self.cur.fetchone()

    def fetchall(self):
        return self.cur.fetchall()

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
