from setuptools import find_packages, setup

VERSION = '4.14.0' #major.minor version aligns with chirpstack-api, patch version can differ

setup(
    name='chirpstack_api_wrapper',
    packages=find_packages(include=['chirpstack_api_wrapper']),
    version=VERSION,
    description='An abstraction layer over the chirpstack_api python library',
    author='waggle',
    maintainer='Francisco Lozano',
    maintainer_email='francisco.lozano@northwestern.edu',
    install_requires=['chirpstack-api==4.14','grpcio==1.*', 'protobuf'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==7.*','pytest-cov==4.*','pytest-xdist==3.*'],
    test_suite='test',
    url='https://github.com/waggle-sensor/chirpstack_api_wrapper',
)