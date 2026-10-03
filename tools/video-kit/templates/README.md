# Genre templates

A demo video is not one shape. A bug fix reads as a failing test, a diff and a passing
test. A benchmark reads as a chart. A phone app reads vertical. Pouring all of them into
one terminal template is the tell that nobody looked at the work.

Each template here is a real project file with a scene spine built for its genre, pacing
that fits, and placeholder narration that shows the focus mechanism. Every one preflights
as it stands. Beside each `.json` is a `.md` that explains why each scene is there and what
to swap.

| Template | Genre | Built around | Aspect |
| --- | --- | --- | --- |
| `product-demo` | the standard hackathon cut | `web` + `code` | 16:9 |
| `bug-fix-pr` | a failing test, the diff, the passing test | `diff` | 16:9 |
| `architecture` | how the system fits together | `diagram` | 16:9 |
| `benchmark` | a claim with numbers | `chart` | 16:9 |
| `cli-tool` | a real command doing real work | `term` | 16:9 |
| `mobile-app` | a phone app, vertical | `web` phone-width (`device` pending) | 9:16 |
| `short` | a vertical cut under 60 seconds | `card` + `web` + `chart` | 9:16 |
| `walkthrough` | code beside its output | `code` + `term` (`compose` pending) | 16:9 |

## Use one

Do not copy by hand. `scaffold.py` picks the genre, claims a free theme and a free
thumbnail layout, inspects your app directory and writes the project file for you:

```bash
python3 scaffold.py my-project ../my-app "The headline." --template bug-fix-pr
```

Run it with no arguments for interactive mode. See `../docs/recipes.md` for worked
examples and `../docs/project-file.md` for every key a template can carry.

## Pending scenes

`mobile-app` and `walkthrough` name a target scene that is not registered yet (`device`
and `compose`). They ship on a scene that works today and preflight now, and each `.md`
says how to swap in the real scene once its module lands. Check what is registered with:

```bash
python3 -c "import style; style.load_scene_modules(); print(style.known())"
```

## The samples

`samples/` holds the small real files the templates point at so they preflight out of the
box: a demo web page with the reveal hook, a before and after pair for the diff, a source
file for the code scene, and two scripts that print real output for the terminal scenes.
Replace every sample path with your own before you build. They are not part of any video.
