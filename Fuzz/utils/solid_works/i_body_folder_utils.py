from typing import List
from pyswx.api.sldworks.interfaces import IBody2, IBodyFolder

__all__ = [
    'get_bodies_in_folder',
]


def get_bodies_in_folder(folder: IBodyFolder, use_cache: bool = True) -> List[IBody2]:
    """
    Get all bodies in a specific body folder.

    Args:
        folder: IBodyFolder instance
        use_cache: whether to use or refresh cache (default True)

    Returns:
        List of IBody2 bodies.

    Cached by folder name.
    """
    if not hasattr(get_bodies_in_folder, 'folder_bodies_cache'):
        setattr(get_bodies_in_folder, 'folder_bodies_cache', {})
    folder_bodies_cache = getattr(get_bodies_in_folder, 'folder_bodies_cache')
    cache_key = folder.get_feature().name
    cached_bodies = folder_bodies_cache.get(cache_key, None)
    if not cached_bodies or use_cache == False:
        cached_bodies = []
        for body_in_folder in folder.get_bodies():
            cached_bodies.append(body_in_folder)
        folder_bodies_cache[cache_key] = cached_bodies
    return cached_bodies
