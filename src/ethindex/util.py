import importlib_metadata


def get_version():
    return importlib_metadata.version("eth-index")
