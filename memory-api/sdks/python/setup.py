"""
BETTY Memory System Python SDK
Official Python client library for BETTY Memory System v2.0
"""

from setuptools import setup, find_packages
import os

# Read the README file
current_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(current_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read version from __init__.py
def get_version():
    version_file = os.path.join(current_directory, 'betty_client', '__init__.py')
    with open(version_file) as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('"')[1]
    return '0.1.0'

setup(
    name='betty-memory-sdk',
    version=get_version(),
    description='Official Python SDK for BETTY Memory System v2.0',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='BETTY Development Team',
    author_email='dev@betty-memory.com',
    url='https://github.com/your-org/betty-python-sdk',
    packages=find_packages(exclude=['tests*', 'examples*']),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Database :: Front-Ends',
    ],
    keywords='betty memory knowledge-management search semantic-search ai',
    python_requires='>=3.9',
    install_requires=[
        'aiohttp>=3.8.0,<4.0.0',
        'pydantic>=2.0.0,<3.0.0',
        'typing-extensions>=4.0.0',
        'yarl>=1.8.0',
        'asyncio-throttle>=1.0.0',
        'backoff>=2.0.0',
        'python-dateutil>=2.8.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'pytest-cov>=4.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.0.0',
            'isort>=5.0.0',
        ],
        'websocket': [
            'websockets>=11.0.0',
            'aiohttp[speedups]>=3.8.0',
        ],
        'cache': [
            'redis>=4.5.0',
            'aioredis>=2.0.0',
        ],
        'all': [
            'websockets>=11.0.0',
            'aiohttp[speedups]>=3.8.0',
            'redis>=4.5.0',
            'aioredis>=2.0.0',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    project_urls={
        'Bug Reports': 'https://github.com/your-org/betty-python-sdk/issues',
        'Source': 'https://github.com/your-org/betty-python-sdk',
        'Documentation': 'https://docs.betty-memory.com/python-sdk',
    },
)