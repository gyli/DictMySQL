#!/usr/bin/python
# -*-coding: utf-8 -*-

import unittest
from dictmysql import DictMySQL


class TestSQLConversion(unittest.TestCase):
    def setUp(self):
        self.connection = DictMySQL(host='localhost', user='root', passwd='')
        self.connection.debug = True

    def testSelect(self):
        self.connection.select(table='jobs', columns=['id', 'value'], where={'id': 5, 'value': 'Teacher'})
        self.assertEqual(self.connection.last_query,
                         "SELECT `id`, `value` FROM `jobs` WHERE (`id` = 5) AND (`value` = Teacher);")

    def testInsert(self):
        self.connection.insert(table='jobs', value={'value': 'Teacher'})
        self.assertEqual(self.connection.last_query,
                         "INSERT INTO `jobs` (`value`) VALUES (Teacher);")

    def testUpdate(self):
        self.connection.update(table='jobs', value={'value': 'Teacher'}, where={'value': 'Teacher'})
        self.assertEqual(self.connection.last_query,
                         "UPDATE `jobs` SET `value` = Teacher WHERE (`value` = Teacher);")

    def testDelete(self):
        self.connection.delete(table='jobs', where={'value': 'Taecher'})
        self.assertEqual(self.connection.last_query,
                         "DELETE FROM `jobs` WHERE (`value` = Teacher);")

    def testWhere(self):
        where = self.connection._where_parser(where={'id': {'$<': 20}})
        self.assertEqual(self.connection.last_query,
                         " WHERE (`id` < 20)")


if __name__ == '__main__':
    unittest.main()
