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
        'httpx>=0.20.0',
        'httpcore>=0.13.7',
        'python-socks>=1.2.4',
    ],
    extras_require={
        'asyncio': ['async-timeout>=3.0.1'],
        'trio': ['trio>=0.16.0'],
        'curio': ['curio>=1.4'],
    }
)
