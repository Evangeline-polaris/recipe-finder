#!/usr/bin/env python3
"""Web server entry point for the Recipe Finder application.

Starts a FastAPI server with uvicorn.  Open ``http://localhost:8000`` in
your browser once the server is running.
"""

import os
import sys
import uvicorn


def main():
    """Launch the web server."""
    # Ensure the project root is on sys.path so that ``src/`` imports work
    project_root = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(project_root, "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    print("=" * 52)
    print("  智能食谱查找器 — Web 服务器")
    print("=" * 52)
    print()
    print("  服务器启动中...")
    print()
    print("  打开浏览器访问: http://localhost:8000")
    print("  API 文档:      http://localhost:8000/docs")
    print()
    print("  按 Ctrl+C 停止服务器")
    print()

    port = int(os.environ.get("PORT", 8000))

    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
        app_dir=src_dir,
    )


if __name__ == "__main__":
    main()