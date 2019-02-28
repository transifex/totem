"""This module contains code that deals with Github."""

from functools import lru_cache
import os

from totem.github.wrappers import GithubService


@lru_cache(maxsize=None)
def github_service() -> GithubService:
    """Return a GithubService instance to use for all Github-related calls.

    Uses an environment variable to get the access token for authentication.
    Caches the object, so that it is used throughout the app.
    """
    return GithubService(os.environ.get('GITHUB_ACCESS_TOKEN', ''))
