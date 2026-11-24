"""Saved briefs: one JSON file, written atomically, with a backup.

Briefs are a writer's working notes — losing them to a half-written
file would be worse than not saving at all. Writes go to a temporary
file in the same folder and are then moved into place, and the previous
version is kept as ``<store>.bak``. A corrupt store is reported, never
silently overwritten.
"""

import json
import os
import tempfile

DEFAULT_STORE = "briefs.json"


class StoreError(Exception):
    """The brief store could not be read or written."""


def load_store(path=DEFAULT_STORE):
    """Load the store. Returns {} if the file does not exist yet."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (ValueError, OSError) as exc:
        raise StoreError("Could not read %s: %s" % (path, exc))
    if not isinstance(data, dict):
        raise StoreError("%s is not a brief store (expected an object)." % path)
    return data


def save_store(data, path=DEFAULT_STORE):
    """Write the store atomically, keeping the previous copy as .bak."""
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=".briefs-", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        if os.path.exists(path):
            try:
                os.replace(path, path + ".bak")
            except OSError:
                pass  # A missing backup is annoying, not fatal.
        os.replace(tmp_path, path)
    except OSError as exc:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise StoreError("Could not write %s: %s" % (path, exc))


def save_brief(brief, path=DEFAULT_STORE):
    """Save one brief (dict or Brief) into the store; returns its id."""
    from .brief import Brief  # local import: avoids a module cycle
    data = load_store(path)
    record = brief.to_dict() if isinstance(brief, Brief) else dict(brief)
    data[record["id"]] = record
    save_store(data, path)
    return record["id"]


def get_brief(brief_id, path=DEFAULT_STORE):
    """Return one brief dict, or None if the id is unknown."""
    return load_store(path).get(brief_id)


def delete_brief(brief_id, path=DEFAULT_STORE):
    """Delete one brief; returns True if something was deleted."""
    data = load_store(path)
    if brief_id not in data:
        return False
    del data[brief_id]
    save_store(data, path)
    return True


def list_briefs(path=DEFAULT_STORE):
    """All saved briefs, newest first."""
    data = load_store(path)
    return sorted(data.values(), key=lambda b: b.get("created", ""),
                  reverse=True)
