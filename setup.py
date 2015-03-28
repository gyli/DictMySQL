#!/usr/bin/python
# -*-coding:UTF-8 -*-

from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='mysqltool',

    # https://packaging.python.org/en/latest/single_source_version.html
    version='0.1.6',

    description='A mysql package above MySQL-python for more convenient database manipulation with Python dictionary.',

    # url='https://github.com/pypa/sampleproject',

    # Author details
    author='Guangyang Li',
    author_email='mail@guangyangli.com',
    license='MIT',
    py_modules=['DictMySQLdb'],
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'
    ],

    # What does your project relate to?
    keywords='mysql database',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['MySQL-python']),

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['MySQL-python'],
)