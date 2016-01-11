#!/usr/bin/python
# -*-coding:UTF-8 -*-

from __future__ import print_function
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
    def _backtick_columns(cols):
        # backtick the former part when it meets the first dot, and then all the rest
        def bt(s):
            if s == '*':
                return ['*']
            elif s:
                return ['`' + s + '`']
            else:
                return []
        return ', '.join(['.'.join(bt(v.split('.')[0]) + bt('.'.join(v.split('.')[1:]))) for v in cols])

    def _backtick(self, value):
        return self._backtick_columns((value,))

    def _tablename_parser(self, table):
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
        # TODO: add function support in where

        if not where:
            return '', ()

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
            '$LIKE': 'LIKE',
            '$BETWEEN': 'BETWEEN',
            '$IN': 'IN'
        }

        _connectors = {
            '$AND': 'AND',
            '$OR': 'OR'
        }

        negative_symbol = {
            '=': '<>',
            '<': '>=',
            '>': '<=',
            '<=': '>',
            '>=': '<',
            '<>': '=',
            'LIKE': 'NOT LIKE',
            'BETWEEN': 'NOT BETWEEN',
            'IN': 'NOT IN',
            'AND': 'OR',
            'OR': 'AND'
        }

        def _get_connector(c, is_not, whitespace=False):
            c = c or '='
            c = negative_symbol.get(c) if is_not else c
            return ' ' + c + ' ' if whitespace else c

        result = {'q': [], 'v': ()}
        placeholder = '%s'

        def _combining(_cond, _operator=None, upper_key=None, connector=None, _not=False):
            if isinstance(_cond, dict):
                i = 1
                for k, v in _cond.items():
                    # {'$AND':{'value':10}}
                    if k.upper() in _connectors:
                        result['q'].append('(')
                        _combining(v, upper_key=upper_key, _operator=_operator, connector=_connectors[k.upper()], _not=_not)
                        result['q'].append(')')
                    # {'>':{'value':10}}
                    elif k.upper() in _operators:
                        _combining(v, _operator=_operators[k.upper()], upper_key=upper_key, connector=connector, _not=_not)
                    # negative
                    elif k.upper() == '$NOT':
                        _combining(v, upper_key=upper_key, _operator=_operator, connector=connector, _not=not _not)
                    # {'value':10}
                    else:
                        _combining(v, upper_key=k, _operator=_operator, connector=connector, _not=_not)
                    # default 'AND' except for the last one
                    if i < len(_cond):
                        result['q'].append(_get_connector('AND', is_not=_not, whitespace=True))
                    i += 1

            elif isinstance(_cond, list):
                # [{'age': {'$>': 22}}, {'amount': {'$<': 100}}]
                if all(isinstance(c, dict) for c in _cond):
                    l_index = 1
                    for l in _cond:
                        _combining(l, _operator=_operator, upper_key=upper_key, connector=connector, _not=_not)
                        if l_index < len(_cond):
                            result['q'].append(_get_connector(connector, is_not=_not, whitespace=True))
                        l_index += 1
                elif _operator in ['=', '$IN'] or not _operator:
                    s_q = self._backtick(upper_key) + (' NOT' if _not else '') + ' IN (' + ', '.join(['%s']*len(_cond)) + ')'
                    result['q'].append('(' + s_q + ')')
                    result['v'] += tuple(_cond)
                elif _operator == 'BETWEEN':
                    s_q = self._backtick(upper_key) + (' NOT' if _not else '') + ' BETWEEN ' + ' AND '.join(['%s']*len(_cond))
                    result['q'].append('(' + s_q + ')')
                    result['v'] += tuple(_cond)
                elif _operator == 'LIKE':
                    s_q = ' OR '.join(['(' + self._backtick(upper_key) + (' NOT' if _not else '') + ' LIKE %s)'] * len(_cond))
                    result['q'].append('(' + s_q + ')')
                    result['v'] += tuple(_cond)
                # if keyword not in prefilled list but value is not dict also, should return error

            elif not _cond:
                s_q = self._backtick(upper_key) + ' IS' + (' NOT' if _not else '') + ' NULL'
                result['q'].append('(' + s_q + ')')
            else:
                s_q = ' '.join([self._backtick(upper_key), _get_connector(_operator, is_not=_not), placeholder])
                result['q'].append('(' + s_q + ')')
                result['v'] += (_cond,)

        _combining(where)
        # TODO: move the WHERE keyword here
        return ' WHERE ' + ''.join(result['q']), result['v']

    @staticmethod
    def _limit_parser(limit=None):
        if isinstance(limit, list) and len(limit) == 2:
            return ' '.join((' LIMIT', ', '.join(str(l) for l in limit)))
        elif str(limit).isdigit():
            return ' '.join((' LIMIT', str(limit)))
        else:
            return ''

    @staticmethod
    def _whitespace_decorator(s, p=True, n=False):
        return ''.join((' ' if p else '', s, ' ' if n else ''))

    def select(self, table, columns, join=None, where=None, order=None, limit=None):
        """
        Example: db.select(tablename='jobs', condition={'id': (2, 3), 'sanitized': None}, columns=['id','value'])
        :type table: string
        :type columns: list
        :type join: dict
        :param join: {'[>]table1(t1)': {'user.id': 't1.user_id'}}
        :type where: dict
        :type limit: int|list
        :param limit: The max row number you want to get from the query.
        """
        if where:
            where_q, _args = self._where_parser(where)
        else:
            _args = None
            where_q = ''

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

        _sql = ''.join(['SELECT ', self._backtick_columns(columns),
                        ' FROM ', self._tablename_parser(table)['formatted_tablename'],
                        join_q,
                        where_q,
                        self._whitespace_decorator(order) if order else '',
                        self._limit_parser(limit), ';'])

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
        select_result = self.select(table=table, columns=[column], join=join, where=where, limit=1)

        if self.debug:
            return select_result
        else:
            result = select_result[0]

        if result:
            return result[0 if self.cursorclass is pymysql.cursors.Cursor else column]
        else:
            if ifnone:
                raise ValueError(ifnone)
            if insert:
                if any([isinstance(d, dict) for d in where.values()]):
                    raise ValueError("The where parameter in get() doesn't support nested condition with insert==True.")
                return self.insert(table=table, value=where)
        return None

    def insert(self, table, value, ignore=False, commit=True):
        """
        Insert a dict into db.
        :return: int. The row id of the insert.
        """
        # TODO: add function support in insert values
        if not isinstance(value, dict):
            raise TypeError('Input value should be a dictionary')

        _sql = ''.join(['INSERT', ' IGNORE' if ignore else '', ' INTO ', self._backtick(table),
                        ' (', self._backtick_columns(value), ') VALUES (', ', '.join(['%s'] * len(value)), ');'])
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
                        ' (', self._backtick_columns(columns), ') VALUES (', ', '.join(['%s'] * len(columns)), ');'])
        _args = tuple(value)

        if self.debug:
            return _sql % _args

        self.cur.executemany(_sql, _args)
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def update(self, table, value, where, commit=True):
        """
        Example: db.update(tablename='jobs', value={'value': 'MECHANIC'}, condition={'id': 3}).
        """
        # TODO: join support
        if where:
            where_q, _args = self._where_parser(where)
        else:
            _args = None
            where_q = ''

        _sql = ''.join(['UPDATE ', self._backtick(table),
                        ' SET ', self._concat_values(value),
                        where_q, ';'])

        if self.debug:
            return _sql % _args

        result = self.cur.execute(_sql, _args)
        if commit:
            self.commit()
        return result

    def upsert(self, table, value, update_columns=None, commit=True):
        """
        Example: db.upsert(tablename='jobs', value={'id': 3, 'value': 'MECHANIC'}).
        :type update_columns: list
        :param update_columns: specify the columns will be updated if record exists
        """
        if not isinstance(value, dict):
            raise TypeError('Input value should be a dictionary')

        if not update_columns:
            update_columns = value.keys()

        _sql = ''.join(['INSERT INTO ', self._backtick(table), ' (', self._backtick(value), ') VALUES ',
                        '(', ', '.join(['%s'] * len(value)), ') ',
                        'ON DUPLICATE KEY UPDATE ', ', '.join([k + '=VALUES(' + k + ')' for k in update_columns]), ';'])
        _args = tuple(value.values())

        if self.debug:
            return _sql % _args

        self.cur.execute(_sql, _args)
        if commit:
            self.conn.commit()
        return self.cur.lastrowid

    def delete(self, table, where, commit=True):
        """
        Example: db.delete(tablename='jobs', condition={'value': ('FACULTY', 'MECHANIC'), 'sanitized': None}).
        """
        if where:
            where_q, _args = self._where_parser(where)
        else:
            _args = None
            where_q = ''
        _sql = ''.join(['DELETE FROM ', self._backtick(table), where_q, ';'])

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
