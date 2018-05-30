from setuptools import find_packages, setup
from drf_channels import __version__

setup(
    name='drf_channels',
    version=__version__,
    url='https://github.com/linuxlewis/channels-api',
    author='Rieljun Liguid',
    author_email='me@iamriel.com',
    description='Simple Resource binding and Consumer Mixin for Django Rest Framework and Channels 2',
    long_description=open('README.rst').read(),
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=1.11',
        'channels>=2.0',
        'djangorestframework>=3.0'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
