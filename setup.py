"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="eth-index",
    setup_requires=["setuptools_scm"],
    use_scm_version=True,
    description="Indexer for the ethereum blockchain",
    long_description=long_description,
    # The project's main homepage.
    url="https://github.com/trustlines-protocol/py-eth-index",
    # Author details
    author="Trustlines-Network",
    author_email="contact@brainbot.com",
    # Choose your license
    license="MIT",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 2 - Pre-Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    # What does your project relate to?
    keywords="ethereum indexer database",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=["web3>=4.4.1", "psycopg2>=2.7", "click", "attrs"],
    python_requires=">=3.6",
    entry_points="""
    [console_scripts]
    ethindex=ethindex.cli:cli
    """,
)
