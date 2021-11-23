import codecs
import os
import re
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = None

with codecs.open(os.path.join(os.path.abspath(os.path.dirname(
        __file__)), 'httpx_socks', '__init__.py'), 'r', 'latin1') as fp:
    try:
        version = re.findall(r"^__version__ = '([^']+)'\r?$",
                             fp.read(), re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')

if sys.version_info < (3, 6, 1):
    raise RuntimeError('httpx_socks requires Python 3.6.1+')

with open('README.md') as f:
    long_description = f.read()

setup(
    name='httpx-socks',
    author='Roman Snegirev',
    author_email='snegiryev@gmail.com',
    version=version,
    license='Apache 2',
    url='https://github.com/romis2012/httpx-socks',
    description='Proxy (HTTP, SOCKS) transports for httpx',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['httpx_socks'],
    keywords='httpx asyncio socks socks5 socks4 http proxy',
    install_requires=[
        'httpx>=0.21.0,<0.22.0',
        'httpcore>=0.14.0,<0.15.0',
        'python-socks>=2.0.0',
    ],
    extras_require={
        'asyncio': ['async-timeout>=3.0.1'],
        'trio': ['trio>=0.16.0'],
    }
)
