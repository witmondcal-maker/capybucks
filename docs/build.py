from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Sphinx writes pages under dest/<lang>/ because root_doc is en/index or
# pt/index. After we hoist that folder, those pages sit one level higher
# than Sphinx expected, so root assets are one `../` too far.
_HOISTED_ASSET = re.compile(
    r'(?P<attr>href|src)=(?P<q>["\'])'
    r"(?P<up>(?:\.\./)+)"
    r"(?P<rest>(?:_static/|_modules/|_images/|_sources/"
    r"|search\.html|genindex\.html|py-modindex\.html)[^\"']*)"
    r"(?P=q)"
)

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "_build" / "html"


def docs_prefix() -> str:
    return os.environ.get("DOCS_PREFIX", "/capybucks").rstrip("/")


def flatten_lang_dir(dest: Path, lang: str) -> list[Path]:
    """Sphinx writes lang/index.md to dest/lang/; hoist it to dest/."""
    nested = dest / lang
    moved: list[Path] = []
    if not nested.is_dir():
        return moved
    for item in nested.iterdir():
        target = dest / item.name
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.move(str(item), str(target))
        moved.append(target)
    nested.rmdir()
    return moved


def _strip_one_parent(match: re.Match[str]) -> str:
    up = match.group("up")[3:]
    attr, quote, rest = match.group("attr", "q", "rest")
    return f"{attr}={quote}{up}{rest}{quote}"


def rewrite_hoisted_asset_paths(html: str) -> str:
    """Drop one `../` from links to Sphinx root assets after flatten."""
    return _HOISTED_ASSET.sub(_strip_one_parent, html)


def rewrite_moved_html(moved: list[Path]) -> None:
    files: list[Path] = []
    for path in moved:
        if path.is_dir():
            files.extend(path.rglob("*.html"))
        elif path.suffix == ".html":
            files.append(path)
    for html_path in files:
        original = html_path.read_text(encoding="utf-8")
        updated = rewrite_hoisted_asset_paths(original)
        if updated != original:
            html_path.write_text(updated, encoding="utf-8")


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
    moved = flatten_lang_dir(dest, lang)
    rewrite_moved_html(moved)


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
