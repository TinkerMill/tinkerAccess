# noinspection PyBroadException
# noinspection PyUnresolvedReferences,PyClassHasNoInit


class PackageInfo:
    python_package_name = 'tinker_access_client'
    pip_package_name = python_package_name.replace('_', '-')
    version = None

    try:
        from version import __version__ as version
    except:
        pass
