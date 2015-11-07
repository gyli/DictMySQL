#!/usr/bin/python
# -*-coding:UTF-8 -*-

from setuptools import setup, find_packages
from os import path
import sys

if sys.version_info[0] >= 3:
    install_requires = ["PyMySQL"]
else:
    install_requires = ["MySQL-python"]

here = path.abspath(path.dirname(__file__))

setup(
    name='dictmysqldb',

    version='0.3.4',

    description='A mysql package on the top of MySQL-python for more convenient database manipulations with Python dictionary.',

    author='Guangyang Li',

    author_email='mail@guangyangli.com',

    license='MIT',

    py_modules=['dictmysqldb'],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
    ],

    keywords='mysql database',
    
    download_url = 'https://github.com/ligyxy/DictMySQLdb',

    install_requires=install_requires
)
