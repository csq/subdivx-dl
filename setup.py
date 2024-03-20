from setuptools import setup

long_description = open('README.md').read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='subdivx-dl',
    version='2024.03.20',
    url='https://github.com/csq/subdivx-dl',
    license='GPLv3+',
    description='A subtitle downloader for the website subdvix.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=['subdivx_dl'],
    py_modules=['subdivx_dl.utils'],
    install_requires=requirements,
    entry_points={
        'console_scripts':[
            'subdivx-dl=subdivx_dl.main:main'
        ]
    },
)