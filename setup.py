import os
import re
import sys

from setuptools import setup

if sys.version_info < (3, 6, 1):
    raise RuntimeError('httpx_socks requires Python 3.6.1+')


def get_version():
    here = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(here, 'httpx_socks', '__init__.py')
    contents = open(filename).read()
    pattern = r"^__version__ = '(.*?)'$"
    return re.search(pattern, contents, re.MULTILINE).group(1)


def get_long_description():
    with open('README.md', mode='r', encoding='utf8') as f:
        return f.read()


setup(
    name='httpx-socks',
    author='Roman Snegirev',
    author_email='snegiryev@gmail.com',
    version=get_version(),
    license='Apache 2',
    url='https://github.com/romis2012/httpx-socks',
    description='Proxy (HTTP, SOCKS) transports for httpx',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    packages=['httpx_socks'],
    keywords='httpx asyncio socks socks5 socks4 http proxy',
    install_requires=[
        'httpx>=0.28.0,<0.29.0',
        'httpcore>=1.0,<2.0',
        'python-socks>=2.0.0',
    ],
    extras_require={
        'asyncio': ['async-timeout>=3.0.1'],
        'trio': ['trio>=0.16.0'],
    },
)
