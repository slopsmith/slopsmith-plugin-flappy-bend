"""Flappy Bend — asset routes.

The Slopsmith plugin loader only serves the manifest-declared files
(screen.html, screen.js, settings.html, tour.json) — anything else has
to come through a plugin-owned route. This module exposes:

    GET /api/plugins/flappy_bend/assets/{path:path}

Path is constrained to the plugin directory (no `..`, no absolute paths,
no symlinks escaping). Mime types are inferred from the extension.
"""

from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse, Response


_MIME_OVERRIDES = {
    ".json": "application/json",
    ".js":   "application/javascript",
    ".svg":  "image/svg+xml",
    ".ogg":  "audio/ogg",
    ".mp3":  "audio/mpeg",
    ".wav":  "audio/wav",
    ".mid":  "audio/midi",
    ".midi": "audio/midi",
    ".woff":  "font/woff",
    ".woff2": "font/woff2",
    ".ttf":   "font/ttf",
    ".otf":   "font/otf",
}


def setup(app, context):
    plugin_dir = Path(__file__).resolve().parent

    @app.get("/api/plugins/flappy_bend/assets/{path:path}")
    def asset(path: str):
        # Reject obvious traversal attempts before touching the FS.
        if not path or path.startswith("/") or ".." in path.split("/") or "\\" in path:
            raise HTTPException(status_code=400, detail="invalid path")
        target = (plugin_dir / path).resolve()
        try:
            target.relative_to(plugin_dir)
        except ValueError:
            raise HTTPException(status_code=400, detail="path escapes plugin dir")
        if not target.is_file():
            raise HTTPException(status_code=404, detail="not found")
        ext = target.suffix.lower()
        mime = _MIME_OVERRIDES.get(ext)
        if mime is None:
            return FileResponse(str(target))
        # FileResponse + media_type honours the override and sets
        # Content-Length / cache headers correctly.
        return FileResponse(str(target), media_type=mime)
