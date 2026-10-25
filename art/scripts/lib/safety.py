"""File safety for Blender scripts: everything stays inside art/, and any .blend
we are about to overwrite is copied to art/blender/backups/ first."""
import shutil
import time
from pathlib import Path

import bpy

ART = Path(__file__).resolve().parents[2]          # <repo>/art
REPO = ART.parent
BACKUPS = ART / "blender" / "backups"


def inside(path, root):
    path, root = Path(path).resolve(), Path(root).resolve()
    return root == path or root in path.parents


def guard(path, root=ART):
    """Refuse to touch files outside `root` (art/ by default)."""
    if not inside(path, root):
        raise PermissionError(f"refusing to write outside {root}: {path}")
    return Path(path).resolve()


def backup(path):
    """Copy an existing .blend to backups/<stem>-<timestamp>.blend. Returns the copy or None."""
    path = guard(path)
    if not path.exists():
        return None
    BACKUPS.mkdir(parents=True, exist_ok=True)
    dest = BACKUPS / f"{path.stem}-{time.strftime('%Y%m%d-%H%M%S')}.blend"
    shutil.copy2(path, dest)
    print(f"[backup] {path.name} -> {dest.relative_to(REPO)}")
    return dest


def fresh_scene():
    """Start from an empty in-memory scene. Touches no files."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def save(path):
    """Back up, then save the current file to `path` (must be inside art/)."""
    path = guard(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    backup(path)
    bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
    print(f"[save] {path.relative_to(REPO)}")
