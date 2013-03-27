from setuptools import setup, find_packages


setup(
    name="statvent",
    version="1.0.1",
    packages=find_packages(),
    author="Christian Wyglendowski",
    author_email="christian@dowski.com",
    description="A simple library that writes stats about your program to a named pipe.",
    license="BSD",
    keywords="monitoring stats statistics counters pipe",
    url="https://github.com/dowski/statvent/",
    long_description=open('README.rst').read(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: C",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Monitoring",
    ],
)
