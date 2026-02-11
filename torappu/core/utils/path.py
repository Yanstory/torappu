def hg_normalize_url(path: str) -> str:
    return path.replace("\\", "/").replace("/", "_").replace("#", "__")
