from setuptools import setup

long_description = open('README.md').read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='subdivx-dl',
    version='2022.07.31',
    url='https://github.com/csq/subdivx-dl',
    description='A subtitle downloader for the website subdvix.com',
    long_description=long_description,
    long_description_content_type='text/markdown',
    package_dir={'': 'subdivx-dl'},
    packages=setuptools.find_packages(where='subdivx-dl'),
    install_requires=requirements,
    entry_points={
        'console_scripts':[
            'subdivx-dl=main:main'
        ]
    },
)