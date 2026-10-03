"""Start a new video from a genre template, on a free theme, ready to build.

    python3 scaffold.py <id> <app-dir> "Headline" --template product-demo

    # flags, all optional:
    #   --template <genre>   product-demo, bug-fix-pr, architecture, benchmark,
    #                        cli-tool, mobile-app, short, walkthrough
    #   --aspect <ratio>     16:9, 9:16, 1:1, 4:5
    #   --quality <name>     draft, standard, high, max
    #   --palette <name>     override the auto-claimed theme

Run it with no arguments, or with pieces missing, and it asks: which genre, which aspect,
which palette. It copies the matching template from templates/, claims a free theme and a
free thumbnail layout (failing loudly if none is free rather than doubling up), inspects
the app directory to suggest a scene spine, writes projects/<id>.json, validates it and
prints the exact next commands.

The written file points at the template's own sample files so it preflights and renders as
it stands. Replace those sample paths with your app's real URL, source files and commands.
The scaffold prints which lines to change based on what it found in the app directory.

Record the claimed theme and layout in work/VIDEO-THEMES.md. preflight.py refuses two
projects on the same theme or the same non-stack thumbnail layout.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import theme

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"

GENRES = [
    "product-demo", "bug-fix-pr", "architecture", "benchmark",
    "cli-tool", "mobile-app", "short", "walkthrough",
]
ASPECTS = ["16:9", "9:16", "1:1", "4:5"]
QUALITIES = ["draft", "standard", "high", "max"]


def free_theme() -> str:
    """The first palette no project has claimed. Fails loudly when the roster is full."""
    taken = {
        json.loads(path.read_text(encoding="utf-8")).get("palette")
        for path in (ROOT / "projects").glob("*.json")
    }
    for name in theme.PALETTES:
        if name not in taken:
            return name
    raise SystemExit(
        "every theme is claimed. Add a palette to theme.py (bright ends, an accent dark "
        "enough to read on the near-white panel, a pale mark) rather than reusing one."
    )


def free_layout() -> str:
    """The first thumbnail layout no project has claimed, skipping the shared `stack`.

    `stack` is the original layout every pre-2026-09-08 demo holds, so it is never claimed
    exclusively. Every other layout is one per demo, the same rule the palette gets.
    """
    import thumb

    taken: set[str] = set()
    for path in (ROOT / "projects").glob("*.json"):
        spec = json.loads(path.read_text(encoding="utf-8")).get("upload")
        if spec:
            taken.add(spec.get("thumbnail", {}).get("layout", "stack"))
    for name in sorted(thumb.LAYOUTS):
        if name != "stack" and name not in taken:
            return name
    raise SystemExit(
        "every thumbnail layout is claimed. Add one to thumb.LAYOUTS rather than doubling "
        "up, then look at the free frame by eye before committing to it."
    )


def ask(prompt: str, options: list[str], default: str) -> str:
    """One interactive choice, with a numbered list and a default on empty input."""
    print(f"\n{prompt}")
    for index, option in enumerate(options, 1):
        mark = "  (default)" if option == default else ""
        print(f"  {index}. {option}{mark}")
    raw = input(f"choose 1-{len(options)} or a name [{default}]: ").strip()
    if not raw:
        return default
    if raw.isdigit() and 1 <= int(raw) <= len(options):
        return options[int(raw) - 1]
    if raw in options:
        return raw
    print(f"  not one of the options, using {default}")
    return default


def inspect_app(app: Path) -> list[str]:
    """Look at the target directory and suggest a scene spine from what is there.

    This is the difference between a template and a starting point that fits the project:
    a repo with tests wants a terminal scene running them, a git repo wants a diff, a web
    app wants a web scene against its dev server.
    """
    notes: list[str] = []
    if not app.exists():
        return [f"{app} does not exist yet, so nothing was inspected. The template's sample "
                "paths stand in until you point the scenes at your app."]

    package = app / "package.json"
    if package.exists():
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
            scripts = data.get("scripts", {})
        except (ValueError, OSError):
            scripts = {}
        for name in ("dev", "start", "serve", "preview"):
            if name in scripts:
                notes.append(
                    f"package.json has a `{name}` script, so a `web` scene against the dev "
                    f"server fits. Run `npm run {name}`, then point the web scene's `url` at it."
                )
                break
        if "test" in scripts:
            notes.append(
                "package.json has a `test` script, so a `term` scene running `npm test` fits."
            )

    if (app / ".git").exists():
        notes.append(
            "this is a git repo, so a `diff` scene fits: point it at "
            "`\"repo\": \"" + str(app) + "\", \"rev\": \"HEAD~1..HEAD\"` to draw the last change."
        )

    test_dirs = [d for d in ("tests", "test", "spec", "__tests__") if (app / d).is_dir()]
    if (app / "pyproject.toml").exists() or (app / "setup.py").exists() or test_dirs:
        where = test_dirs[0] if test_dirs else "the test suite"
        notes.append(
            f"there is a Python project or a {where} directory, so a `term` scene running "
            "`pytest -q` fits."
        )

    sources = []
    for pattern in ("*.py", "src/*.py", "src/*.ts", "src/*.js", "*.ts", "*.rs", "*.go"):
        sources.extend(sorted(app.glob(pattern))[:1])
    if sources:
        notes.append(
            f"a `code` scene can read a real source file, for example {sources[0]}."
        )

    if not notes:
        notes.append(
            "nothing obvious to inspect (no package.json, no .git, no tests). The template's "
            "sample paths stand in until you point the scenes at your app."
        )
    return notes


def validate(path: Path) -> list[str]:
    """Validate the written file. Calls schema.py if it exists yet, defensively.

    schema.py is written by another hand and may not be present. When it is, its check runs
    and its findings are returned. When it is not, a small built-in check runs instead so a
    scaffold is never shipped without at least a shape check.
    """
    problems: list[str] = []
    try:
        import schema  # type: ignore
    except ModuleNotFoundError:
        schema = None  # type: ignore
    if schema is not None:
        for name in ("validate", "check", "check_project"):
            fn = getattr(schema, name, None)
            if callable(fn):
                try:
                    result = fn(path)
                except TypeError:
                    result = fn(json.loads(path.read_text(encoding="utf-8")))
                if isinstance(result, (list, tuple)):
                    problems.extend(str(item) for item in result)
                elif result:
                    problems.append(str(result))
                return problems

    # Built-in fallback: the shape build.py and preflight.py both rely on.
    project = json.loads(path.read_text(encoding="utf-8"))
    if not project.get("id"):
        problems.append("no id")
    if not isinstance(project.get("segments"), list) or not project["segments"]:
        problems.append("no segments")
    for index, segment in enumerate(project.get("segments", [])):
        if "type" not in segment:
            problems.append(f"segment {index} has no type")
    return problems


def scaffold(project_id: str, app: Path, headline: str, genre: str,
             aspect: str, quality: str, palette: str | None) -> Path:
    out = ROOT / "projects" / f"{project_id}.json"
    if out.exists():
        raise SystemExit(f"{out} already exists, edit it instead")

    template_path = TEMPLATES / f"{genre}.json"
    if not template_path.exists():
        raise SystemExit(f"no template for genre {genre!r}, have {', '.join(GENRES)}")

    project = json.loads(template_path.read_text(encoding="utf-8"))
    palette = palette or free_theme()
    if palette not in theme.PALETTES:
        raise SystemExit(f"unknown palette {palette!r}, have {', '.join(sorted(theme.PALETTES))}")
    layout = free_layout()

    # Rewrite the identity, keep the template's scene spine.
    project.pop("note", None)
    project["id"] = project_id
    project["palette"] = palette
    project["header"] = f"{project_id}  ~  {app.name}"
    if aspect != "16:9":
        style = dict(project.get("style", {}))
        style["aspect"] = aspect
        project["style"] = style
    elif "style" in project and project["style"].get("aspect") == "16:9":
        project["style"].pop("aspect", None)
        if not project["style"]:
            project.pop("style")
    if quality != "standard":
        render = dict(project.get("render", {}))
        render["quality"] = quality
        project["render"] = render

    # Drop the headline into the first card.
    for segment in project["segments"]:
        if segment.get("type") == "card":
            segment["lines"] = [headline]
            break

    project.setdefault("upload", {})
    if isinstance(project["upload"], dict):
        project["upload"].pop("note", None)
        project["upload"].setdefault("thumbnail", {})["layout"] = layout

    out.write_text(json.dumps(project, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    field = theme.palette(palette).get("field", "vertical")
    print(f"\n{out}")
    print(f"  genre     {genre}")
    print(f"  theme     {palette} ({field} field), claimed because it was free")
    print(f"  layout    {layout} thumbnail, claimed because it was free")
    print(f"  aspect    {aspect}   quality {quality}")

    print("\nwhat the app directory suggests:")
    for note in inspect_app(app):
        print(f"  - {note}")

    problems = validate(out)
    if problems:
        print("\nvalidation found problems:")
        for problem in problems:
            print(f"  FAIL {problem}")
    else:
        print("\nvalidation clean.")

    print("\nnext:")
    print(f"  1. record the theme and layout in work/VIDEO-THEMES.md")
    print(f"  2. read templates/{genre}.md, then replace the sample paths in "
          f"projects/{project_id}.json with your app's real URL, files and commands")
    print(f"  3. python3 preflight.py projects/{project_id}.json")
    print(f"  4. python3 frame.py projects/{project_id}.json 10 30")
    print(f"  5. MUSIC=<licensed track> python3 build.py projects/{project_id}.json")
    print(f"  6. python3 upload.py projects/{project_id}.json")
    return out


def main(argv: list[str]) -> None:
    positional: list[str] = []
    flags: dict[str, str] = {}
    index = 0
    while index < len(argv):
        token = argv[index]
        if token.startswith("--"):
            key = token[2:]
            if "=" in key:
                name, value = key.split("=", 1)
                flags[name] = value
            else:
                index += 1
                flags[key] = argv[index] if index < len(argv) else ""
        else:
            positional.append(token)
        index += 1

    interactive = len(positional) < 2

    if positional:
        project_id = positional[0]
    else:
        project_id = input("project id (short, kebab-case): ").strip()
    if not project_id:
        raise SystemExit("a project id is required")

    if len(positional) >= 2:
        app = Path(positional[1]).expanduser().resolve()
    else:
        raw = input("app directory (the project this video shows): ").strip()
        app = Path(raw).expanduser().resolve() if raw else ROOT

    headline = positional[2] if len(positional) >= 3 else ""
    if not headline:
        headline = input("headline (one line) [TODO: the headline.]: ").strip() or "TODO: the headline."

    genre = flags.get("template")
    if genre is None:
        genre = ask("which genre?", GENRES, "product-demo") if interactive else "product-demo"
    if genre not in GENRES:
        raise SystemExit(f"unknown genre {genre!r}, have {', '.join(GENRES)}")

    aspect = flags.get("aspect")
    if aspect is None:
        default_aspect = "9:16" if genre in ("short", "mobile-app") else "16:9"
        aspect = ask("which aspect?", ASPECTS, default_aspect) if interactive else default_aspect
    if aspect not in ASPECTS:
        raise SystemExit(f"unknown aspect {aspect!r}, have {', '.join(ASPECTS)}")

    quality = flags.get("quality", "standard")
    if quality not in QUALITIES:
        raise SystemExit(f"unknown quality {quality!r}, have {', '.join(QUALITIES)}")

    palette = flags.get("palette")
    if palette is None and interactive:
        options = [name for name in theme.PALETTES]
        taken = {
            json.loads(path.read_text(encoding="utf-8")).get("palette")
            for path in (ROOT / "projects").glob("*.json")
        }
        free = [name for name in options if name not in taken]
        suggested = free[0] if free else options[0]
        choice = ask("which palette? (free ones only, blank auto-claims)",
                     free or options, suggested)
        palette = choice

    scaffold(project_id, app, headline, genre, aspect, quality, palette)


if __name__ == "__main__":
    main(sys.argv[1:])
