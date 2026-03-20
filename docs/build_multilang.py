from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
SOURCE_DIR = DOCS_DIR / "source"
BUILD_DIR = DOCS_DIR / "build" / "html"
DOCTREE_DIR = DOCS_DIR / "build" / "doctrees"
LANGUAGES = {
    "en": "English",
    "ko": "한국어",
}

LANDING_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>UR Dashboard Documentation</title>
  <style>
    :root {
      color-scheme: light dark;
      font-family: -apple-system, BlinkMacSystemFont, \"Segoe UI\", sans-serif;
    }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: #f7f7f7;
      color: #111827;
    }
    .card {
      width: min(560px, calc(100vw - 32px));
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 16px;
      padding: 28px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
    }
    h1 {
      margin: 0 0 8px;
      font-size: 28px;
    }
    p {
      margin: 0 0 18px;
      line-height: 1.6;
    }
    .links {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .links a {
      text-decoration: none;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid #d1d5db;
      color: inherit;
      font-weight: 600;
    }
    .hint {
      margin-top: 16px;
      color: #6b7280;
      font-size: 14px;
    }
    @media (prefers-color-scheme: dark) {
      body {
        background: #111827;
        color: #f9fafb;
      }
      .card {
        background: #1f2937;
        border-color: #374151;
      }
      .links a {
        border-color: #4b5563;
      }
      .hint {
        color: #d1d5db;
      }
    }
  </style>
  <script>
    (function () {
      var lang = (navigator.language || navigator.userLanguage || '').toLowerCase();
      if (lang.indexOf('ko') === 0) {
        window.location.replace('./ko/index.html');
      } else {
        window.location.replace('./en/index.html');
      }
    }());
  </script>
</head>
<body>
  <main class="card">
    <h1>UR Dashboard Documentation</h1>
    <p>Select your preferred language.</p>
    <div class="links">
      <a href="./en/index.html">English</a>
      <a href="./ko/index.html">한국어</a>
    </div>
    <p class="hint">If automatic redirection does not work, use one of the links above.</p>
  </main>
</body>
</html>
"""


def run_build(language: str) -> None:
    output_dir = BUILD_DIR / language
    doctree_dir = DOCTREE_DIR / language
    source_dir = SOURCE_DIR / language

    output_dir.mkdir(parents=True, exist_ok=True)
    doctree_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "-b",
        "html",
        "-c",
        str(SOURCE_DIR),
        "-D",
        f"language={language}",
        str(source_dir),
        str(output_dir),
        "-d",
        str(doctree_dir),
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    if DOCTREE_DIR.exists():
        shutil.rmtree(DOCTREE_DIR)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    for language in LANGUAGES:
        run_build(language)

    (BUILD_DIR / "index.html").write_text(LANDING_PAGE, encoding="utf-8")
    (BUILD_DIR / ".nojekyll").write_text("", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
