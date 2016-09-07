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
)
