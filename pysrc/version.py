def GET_VERSION() -> str:
    try:
        from importlib.metadata import version, PackageNotFoundError
        try:
            return version("mylange")
        except PackageNotFoundError:
            return "unknown"
    except ImportError:
        return "unknown"