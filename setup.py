from setuptools import find_packages, setup

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    name='needle',
    packages=find_packages(),
    version='0.1.0',
    author="Thread Tech",
    author_email="tech@thread.com",
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: Open Source :: MIT',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Office/Business',
    ),
    url='https://github.com/thread/needle',
    install_requires=(
        'aiohttp >=0.22',
        'numpy >=1.11, <2',
        'scipy >=0.18',
        'pyyaml >=3.12, <4',
        'python-dateutil >=2.5',
        'Jinja2 >=2.8',
    ),
    entry_points={
        'console_scripts': (
            'needle = needle.cli:main',
        ),
    },
)
