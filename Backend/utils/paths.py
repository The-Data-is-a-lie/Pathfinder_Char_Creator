"""Repo-root-anchored paths for the static game data.

The generator reads its data from two roots -- ``Backend/json/**`` (scraped JSON) and ``data/*.csv``
(feat/spell/trait tables) -- and those paths used to be written relative to the *current working
directory*. That only resolved because both entry points called ``os.chdir(repo_root)`` at import
time, a process-wide side effect just to make imports work: anything else in the process (a test
runner, a notebook, a WSGI server) inherited the changed directory.

Resolving against ``__file__`` instead makes every read independent of where the process was
launched from, so the chdir is gone. Most of the JSON loaders under ``class_func/`` already did this
by hand (``flaws.py``, ``spheres.py``, ``race_func.py``, ...); this module is the shared version so
new code has one obvious thing to call.

    from utils.paths import repo_path
    pd.read_csv(repo_path('data/feats.csv'), sep='|')
"""
from pathlib import Path

# utils/paths.py -> utils -> Backend -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]


def repo_path(*parts):
    """Absolute Path for a repo-root-relative path.

    Accepts either a single string ('data/feats.csv', backslashes tolerated) or path segments
    ('Backend', 'json', 'items_broken.json'). An already-absolute path is handed back untouched, so
    callers that accept a caller-supplied location can resolve unconditionally.
    """
    if len(parts) == 1:
        candidate = Path(str(parts[0]).replace('\\', '/'))
        if candidate.is_absolute():
            return candidate
        return REPO_ROOT / candidate
    return REPO_ROOT.joinpath(*parts)
