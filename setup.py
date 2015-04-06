#!/usr/bin/python
# -*-coding:UTF-8 -*-

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='dictmysqldb',

    version='0.1.7',

    description='A mysql package above MySQL-python for more convenient database manipulation with Python dictionary.',

    author='Guangyang Li',

    author_email='mail@guangyangli.com',

    license='MIT',

    py_modules=['DictMySQLdb'],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'
    ],

    keywords='mysql database',

    packages=find_packages(exclude=['MySQL-python']),

    install_requires=['MySQL-python'],
)