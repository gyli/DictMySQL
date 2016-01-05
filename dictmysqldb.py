#!/usr/bin/python
# -*-coding:UTF-8 -*-

import pymysql
import pymysql.cursors
import re


class DictMySQLdb:
    def __init__(self, host, user, passwd, db, port=3306, charset='utf8', init_command='SET NAMES UTF8',
                 dictcursor=False, use_unicode=True):
        self.host = host
        self.port = int(port)
        self.user = user
        self.passwd = passwd
        self.db = db
        self.dictcursor = dictcursor
        self.cursorclass = pymysql.cursors.DictCursor if dictcursor else pymysql.cursors.Cursor
        self.charset = charset
        self.init_command = init_command
        self.use_unicode = use_unicode
        self.conn = pymysql.connect(host=self.host, port=self.port, user=self.user, passwd=self.passwd, db=self.db,
                                    charset=charset, init_command=init_command, cursorclass=self.cursorclass,
                                    use_unicode=self.use_unicode)
        self.cur = self.conn.cursor()
        self.debug = False

    def reconnect(self):
        try:
            self.cursorclass = pymysql.cursors.DictCursor if self.dictcursor else pymysql.cursors.Cursor
            self.conn = pymysql.connect(host=self.host, port=self.port, user=self.user, passwd=self.passwd,
                                        db=self.db, cursorclass=self.cursorclass, charset=self.charset,
                                        init_command=self.init_command,
                                        use_unicode=self.use_unicode)
            self.cur = self.conn.cursor()
            return True
        except pymysql.Error as e:
            print("Mysql Error: %s" % (e,))
            return False

    def query(self, sql, args=None):
        """
        :param sql: string. SQL query.
        :param args: tuple. Arguments of this query.
        """
        try:
            result = self.cur.execute(sql, args)
        except pymysql.Error as e:
            result = None
            print("Mysql Error: %s\nOriginal SQL:%s" % (e, sql))
        return result

    @staticmethod
    def _iterbacktick(value):
        # backtick the former part when it meets the first dot, and then all the rest
        def bt(s):
            return ['`' + s + '`'] if s else []
        return ', '.join(['.'.join(bt(v.split('.')[0]) + bt('.'.join(v.split('.')[1:]))) for v in value])

    def _backtick(self, value):
        return '*' if value == '*' else self._iterbacktick((value,))

    def _tablename_parser(self, table):
        """
        :return: (join_type, table_name, alias)
        """
        result = re.match('^(\[(|>|<|<>|><)\])??(\w+)(\((|\w+)\))??$', table.replace(' ', ''))
        join_type = ''
        alias = ''
        formatted_tablename = self._backtick(table)
        if result:
            alias = result.group(5) if result.group(5) else ''

            tablename = result.group(3)

            formatted_tablename = ' '.join([self._backtick(tablename),
                                            'AS', self._backtick(alias)]) if alias else self._backtick(tablename)

            join_type = {'>': 'LEFT', '<': 'RIGHT', '<>': 'FULL', '><': 'INNER'}.get(result.group(2), '')
        else:
            tablename = table

        return {'join_type': join_type,
                'tablename': tablename,
                'alias': alias,
                'formatted_tablename': formatted_tablename}

    def _concat_values(self, value, placeholder='%s'):
        """
        Return "`id` = %s, `name` = %s". Only used in update(), no need to convert NULL values.
        """
        return ', '.join([' = '.join([self._backtick(v), placeholder]) for v in value])

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
            '$LIKE': 'LIKE'
            # '$BETWEEN': 'BETWEEN',
            # '$IN': 'IN',
            # '$NIN': 'NOT IN'
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
                for k, v in _cond.items():
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
            elif not _cond:
                s_q = self._backtick(upper_key) + ' IS NULL '
                result['q'].append('(' + s_q + ')')
            else:
                if _operator:
                    s_q = self._backtick(upper_key) + ' ' + _operator + ' ' + placeholder
                else:
                    s_q = self._backtick(upper_key) + ' = ' + placeholder
                result['q'].append('(' + s_q + ')')
                result['v'] += (_cond,)

        _combining(where)
        return ''.join(result['q']), result['v']

    def insert(self, table, value, ignore=False, commit=True):
        """
        Insert a dict into db.
        :return: int. The row id of the insert.
        """
        if not isinstance(value, dict):
            raise TypeError('Input value should be a dictionary')

        _sql = ''.join(['INSERT', ' IGNORE' if ignore else '', ' INTO ', self._backtick(table),
                        ' (', self._iterbacktick(value), ') VALUES (', ', '.join(['%s'] * len(value)), ');'])
        _args = tuple(value.values())

        if self.debug:
            return _sql % _args

        self.cur.execute(_sql, _args)
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def insertmany(self, table, columns, value, ignore=False, commit=True):
        """
        Insert multiple records within one query.
        Example: db.insertmany(tablename='jobs', columns=['id', 'value'], value=[('5', 'TEACHER'), ('6', 'MANAGER')]).
        :type value: list
        :param value: Example: [(value_1, value_2,), ].
        :return: int. The row id of the LAST insert only.
        """
        if not isinstance(value, (list, tuple)):
            raise TypeError('Input value should be a list or tuple')

        _sql = ''.join(['INSERT', ' IGNORE' if ignore else '', ' INTO ', self._backtick(table),
                        ' (', self._iterbacktick(columns), ') VALUES (', ', '.join(['%s'] * len(columns)), ');'])
        _args = tuple(value)

        if self.debug:
            return _sql % _args

        self.cur.executemany(_sql, _args)
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def upsert(self, table, value, commit=True):
        """
        Example: db.upsert(tablename='jobs', value={'id': 3, 'value': 'MECHANIC'}).
        """
        if not isinstance(value, dict):
            raise TypeError('Input value should be a dictionary')

        # TODO: specify the columns
        _sql = ''.join(['INSERT INTO ', self._backtick(table), ' (', self._backtick(value), ') VALUES ',
                        '(', ', '.join(['%s'] * len(value)), ') ',
                        'ON DUPLICATE KEY UPDATE ', ', '.join([k + '=VALUES(' + k + ')' for k in value.keys()]), ';'])
        _args = tuple(value.values())

        if self.debug:
            return _sql % _args

        self.cur.execute(_sql, _args)
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def select(self, table, columns, join=None, where=None, order=None, limit=0):
        """
        Example: db.select(tablename='jobs', condition={'id': (2, 3), 'sanitized': None}, columns=['id','value'])
        :type table: string
        :type columns: list
        :type join: dict
        :param join: {'[>]table1(t1)': {'user.id': 't1.user_id'}}
        :type where: dict
        :type limit: int
        :param limit: The max row number you want to get from the query. Default is 0 which means no limit.
        """
        if where:
            where_q, _args = self._where_parser(where)
        else:
            where = {}
            _args = None
            where_q = None

        join_q = ''
        if not join:
            join = {}
        for j_table, j_on in join.items():
            join_table = self._tablename_parser(j_table)
            join_q += ''.join([(' ' + join_table['join_type']) if join_table['join_type'] else '', ' JOIN ',
                               join_table['formatted_tablename'],
                               ' ON ',
                               ' AND '.join(['='.join([self._backtick(o_k),
                                                       self._backtick(o_v)]) for o_k, o_v in j_on.items()])])

        _sql = ''.join(['SELECT ', self._iterbacktick(columns),
                        ' FROM ', self._tablename_parser(table)['formatted_tablename'],
                        join_q,
                        ' WHERE ' + where_q if where else '',
                        ''.join([' LIMIT ', str(limit)]) if limit else '', ';'])

        if self.debug:
            return _sql % _args

        self.cur.execute(_sql, _args)
        return self.cur.fetchall()

    def get(self, table, column, join=None, where=None, insert=False, ifnone=None):
        """
        A simplified method of select, for getting the first result in one column only. A common case of using this
        method is getting id.
        Example: db.get(tablename='jobs', condition={'id': 2}, column='value').
        :type column: str
        :param insert: If insert==True, insert the input condition if there's no result and return the id of new row.
        :param ifnone: When ifnone is a non-empty string, raise an error if query returns empty result. insert parameter
                       would not work in this mode.
        """
        # TODO: use 0 under dict cursor?
        ids = self.select(table=table, columns=[column], join=join, where=where, limit=1)[0]

        if ids:
            return ids[0 if self.cursorclass is pymysql.cursors.Cursor else column]
        else:
            if ifnone:
                raise ValueError(ifnone)
            if insert:
                if any([isinstance(d, dict) for d in where.values()]):
                    raise ValueError("The where parameter in get() doesn't support nested condition with insert==True.")
                return self.insert(table=table, value=where)
        return None

    def update(self, table, value, where, commit=True):
        """
        Example: db.update(tablename='jobs', value={'value': 'MECHANIC'}, condition={'id': 3}).
        """
        # TODO: join support
        if where:
            where_q, _args = self._where_parser(where)
        else:
            where = {}
            _args = None
            where_q = None

        _sql = ''.join(['UPDATE ', self._backtick(table), ' SET ', self._concat_values(value),
                        ' WHERE ' + where_q if where else '', ';'])

        if self.debug:
            return _sql % _args

        result = self.cur.execute(_sql, _args)
        if commit:
            self.commit()
        return result

    def delete(self, table, where, commit=True):
        """
        Example: db.delete(tablename='jobs', condition={'value': ('FACULTY', 'MECHANIC'), 'sanitized': None}).
        """
        if where:
            where_q, _args = self._where_parser(where)
        else:
            where = {}
            _args = None
            where_q = None
        _sql = ''.join(['DELETE FROM ', self._backtick(table), ' WHERE ' + where_q if where else '', ';'])

        if self.debug:
            return _sql % _args

        result = self.cur.execute(_sql, _args)
        if commit:
            self.commit()
        return result

    def now(self):
        query = "SELECT NOW() AS now;"
        if self.debug:
            return query
        self.cur.execute(query)
        return self.cur.fetchone()[0 if self.cursorclass is pymysql.cursors.Cursor else 'now'].strftime(
                "%Y-%m-%d %H:%M:%S")

    def last_insert_id(self):
        query = "SELECT LAST_INSERT_ID() AS lid;"
        if self.debug:
            return query
        self.query(query)
        return self.cur.fetchone()[0 if self.cursorclass is pymysql.cursors.Cursor else 'lid']

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
