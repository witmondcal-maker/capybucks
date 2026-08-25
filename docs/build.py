from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "_build" / "html"


def docs_prefix() -> str:
    return os.environ.get("DOCS_PREFIX", "/capybucks").rstrip("/")


def flatten_lang_dir(dest: Path, lang: str) -> None:
    """Sphinx writes lang/index.md to dest/lang/; hoist it to dest/."""
    nested = dest / lang
    if not nested.is_dir():
        return
    for item in nested.iterdir():
        target = dest / item.name
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.move(str(item), str(target))
    nested.rmdir()


def build(lang: str) -> None:
    dest = HTML / lang
    env = os.environ.copy()
    env["DOC_LANG"] = lang
    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "-b",
        "html",
        str(ROOT),
        str(dest),
    ]
    subprocess.check_call(cmd, env=env)
    flatten_lang_dir(dest, lang)


def write_chooser() -> None:
    prefix = docs_prefix()
    en_href = f"{prefix}/en/" if prefix else "en/"
    pt_href = f"{prefix}/pt/" if prefix else "pt/"
    (HTML / "index.html").write_text(
        f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>capybucks documentation</title>
  <meta http-equiv="refresh" content="0; url={en_href}"/>
</head>
<body>
  <p><a href="{en_href}">English</a> · <a href="{pt_href}">Português</a></p>
</body>
</html>
""",
        encoding="utf-8",
    )
    (HTML / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    if HTML.exists():
        shutil.rmtree(HTML)
    build("en")
    build("pt")
    write_chooser()
    print(f"Built {HTML} (English {docs_prefix() or ''}/en/)")


if __name__ == "__main__":
    main()
