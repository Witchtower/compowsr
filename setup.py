from setuptools import setup

setup(
    name='compowsr',
    packages=['compowsr'],
    include_package_data=True,
    install_packages=['flask', 'praw']
)
