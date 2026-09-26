# WolfsScreenHitter

[English](README.md) | [Português](README.pt.md)

Points your mouse cursor at a **visual target on screen**, found in real time by colour or by a reference image. The click is always yours: the program only positions the cursor, it never clicks.

Two ways to recognise the target, both configured through a JSON file:

- **`shape`** — finds blobs of a colour whose shape is close to a circle. Good for coloured targets, outlines, buttons, indicators.
- **`template`** — locates the image of a letter, symbol, icon or number using multi-scale template matching. Good for reading text on screen.

Runs on Windows, with the target anywhere you choose: a specific window, the central area of that window, the whole screen, the virtual desktop, or a fixed rectangle.

---

## Setup

### 1. Requirements

- Windows 10 or 11
- Python 3.10 or newer (`python --version`)

### 2. Install

```bash
git clone https://github.com/IsmarWolf/WolfsScreenHitter.git
cd WolfsScreenHitter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`opencv-python`, `numpy`, `dxcam` and `mss` are the only dependencies. Nothing else, and no GPU needed.

Optionally install the package itself, which gives you a `wolfs-screen-hitter` command:

```bash
pip install -e .
```

### 3. First run

Start here, before anything else. This checks the detection once and moves nothing:

```bash
python -m wolfs_screen_hitter check profiles/circulo_claro.json --debug out/debug.png
```

Open `out/debug.png`. A green box on your target means the setup works. No box means the target does not match the profile yet — go to [Troubleshooting](#troubleshooting).

Two things to know about what you just ran:

- The example profile uses `region: "screen"`, so it looks at the whole primary screen and expects to see a light round target somewhere in it. If you do not have one on screen right now, it correctly reports nothing. That is not a broken install.
- The detector only sees what is **drawn on screen**. If the target is covered by another window, it does not exist as far as the detector is concerned.

### 4. Run it for real

```bash
python -m wolfs_screen_hitter run profiles/circulo_claro.json
```

Stop with **Esc**, **F12**, or by parking the mouse in the top-left corner for a second.

### 5. Make it yours

Copy one of the example profiles and edit the `target` block. The shipped profiles are:

| Profile | For |
|---|---|
| `profiles/circulo_claro.json` | A light round target, anywhere on screen. Start here. |
| `profiles/faixa_hsv.json` | A target of a specific vivid colour, by HSV range. |
| `profiles/letra_template.json` | A letter, number or icon, by image template. |

The loop is always the same: copy a profile, adjust `target`, test with `check --debug`, repeat. You never need to touch Python. [Tuning a profile](#tuning-a-profile) has the recipes.

---

## Commands

| Command | What it does |
|---|---|
| `check PROFILE` | Looks once, reports, optionally draws a debug image. Moves nothing. |
| `run PROFILE` | Follows the target in a loop and positions the cursor. |
| `capture FILE` | Saves a screenshot of the window that was last focused, or the whole screen if there is no window to grab. |
| `crop SRC DST X Y W H` | Cuts a template out of a screenshot. |
| `list-profiles` | Shows the profiles available. |
| `list-windows` | Lists visible windows with their size and position. |

Flags belong to one command each, and argparse will tell you if you mix them up:

| Flag | On | What it does |
|---|---|---|
| `--debug FILE` | `check` | Saves what the detector saw, with the target boxed. |
| `--tentativas N` | `check` | Retries the detection up to `N` times, `40` by default. |
| `--espera S` | `check` | Pause between those retries, `0.05` seconds by default. |
| `--interval S` | `run` | Pause between frames in the loop, `0.002` seconds by default. |
| `--dry-run` | `run` | Runs the same detection as `check` and never moves the mouse. |
| `--delay S` | `capture` | Waits `S` seconds before grabbing, for a menu you are about to open. |

Two things `run --dry-run` cannot do: it takes no `--debug`, and it always uses the default `--tentativas` and `--espera`. Use `check` when you want a debug image or a longer retry.

---

## How it works

```
wolfs_screen_hitter/
  win.py        Win32 access: cursor, keys, movement dispatch
  capture.py    screen capture (DXGI, falling back to mss)
  windows.py    window enumeration and search-region resolution
  detect.py     the two detectors: shape by colour and template
  profiles.py   loading and validation of JSON profiles
  pointer.py    cursor movement modes
  app.py        main loop and command line
```

The cycle is: capture the region → detect → move the cursor → repeat. DXGI capture takes about 2 ms and detection a few more milliseconds, which gives over a hundred frames per second on a full-screen capture.

Screen capture goes through DXGI first and falls back to `mss` automatically if DXGI is unavailable, such as on some hybrid-graphics laptops.

---

## Works on any screen

The program does not know, and does not need to know, which program is your target. It does not look for a game name or a specific window unless you ask it to.

That means the same configuration works for a game, a video, a chart, a spreadsheet, a PDF, or anything else that draws a target on screen. What the detector sees is pixels, not applications.

### Choosing where to look

It is all the `region` block. Four options, and you swap between them without changing anything else:

| `mode` | Where it looks | When to use |
|---|---|---|
| `screen` | The entire primary screen | The default. Works for most cases. |
| `virtual` | All monitors at once | Target on another monitor, or more than one monitor. |
| `window` | Only the window named by `window.title` | A lot on screen resembles the target. |
| `fixed` | A rectangle you choose | You know exactly where the target appears. |

To use **any monitor**, switch to the whole desktop:

```json
"region": { "mode": "virtual" }
```

To use **only one window**, target it by title and discard the edges with the margin:

```json
"window": { "title": "MyProgram" },
"region": { "mode": "window", "margin": 130 }
```

To pin down **an exact spot**, use coordinates:

```json
"region": { "mode": "fixed", "left": 640, "top": 300, "width": 640, "height": 480 }
```

### Screen or window?

Choosing `screen` is the easiest and most broad, but it has a consequence: the detector sees **everything that is visible**, including the interface of your own programs. If you have a light round icon in the corner of the screen, it is just as valid a candidate as the real target, and the detector will pick the largest one.

When that happens, narrow the search. `margin` is the right tool: it erases a band around the window, discarding the icons, buttons and status bars near the edges.

To find the right margin for your case: start at `0`, run `check` with `--debug`, and look at where the green box landed. If it landed on an edge icon, raise the margin until that icon is cut off. If the box disappeared along with the target, lower it.

To find the exact window title, run `list-windows` and copy the name that shows up. Titles only need to match partially, so `"title": "Paint"` finds `"Paint - picture.png"`.

---

## Profiles

A profile is a JSON file that describes **what to look for, where to look, and how to react**.

### The minimal profile

Most of the time this is all you need:

```json
{
  "detector": "shape",
  "region": { "mode": "screen" },
  "target": {
    "bright": { "v_min": 150, "s_max": 110 },
    "size": { "min": 45, "max": 240 },
    "fill": { "min": 0.04, "max": 0.4 }
  }
}
```

No `window`, no program name: the detector sweeps the screen and finds any light round target that is visible. It is the most generic profile possible, and it is what solves most cases.

### Full structure

Every field, with the default value that applies when you omit it:

```json
{
  "name": "My target",
  "detector": "shape",

  "window": {
    "title": "MyProgram",
    "min_width": 200,
    "min_height": 200
  },

  "region": {
    "mode": "window",
    "margin": 0
  },

  "target": {
    "bright": { "v_min": 150, "s_max": 110 },
    "size":   { "min": 45, "max": 240 },
    "aspect": { "min": 0.65, "max": 1.5 },
    "fill":   { "min": 0.04, "max": 0.4 },
    "work_scale": 0.5
  },

  "pointer": { "mode": "teleport" },
  "controls": { "corner_seconds": 1.0 }
}
```

### `region` — where to look

| Key | Meaning |
|---|---|
| `mode` | `window`, `screen`, `virtual` or `fixed`, as described above. |
| `margin` | Pixels discarded from each edge. Only used by `window`. |
| `left`, `top`, `width`, `height` | The rectangle, only used by `fixed`. |

### `target` — what the target is

Two ways to describe the colour:

```json
"bright": { "v_min": 150, "s_max": 110 }
```

finds light, weakly saturated pixels. `v_min` is the minimum brightness, `s_max` the maximum saturation. A low `s_max` excludes strong red and green, so this combination finds white, grey and beige without catching vivid colour.

```json
"dark": { "v_max": 80, "s_max": 120 }
```

finds dark pixels. You can use `bright` and `dark` together: the target becomes the union of the two.

```json
"hsv_min": [0, 140, 140],
"hsv_max": [12, 255, 255]
```

picks an exact range of hue, saturation and value. `hsv_min` and `hsv_max` replace `bright`/`dark` when present. The values are `[hue, saturation, value]`, and hue runs from 0 to 179 in OpenCV:

| Colour | `hsv_min` | `hsv_max` |
|---|---|---|
| Red | `[0, 140, 140]` | `[10, 255, 255]` |
| Orange/yellow | `[11, 140, 140]` | `[30, 255, 255]` |
| Green | `[35, 90, 90]` | `[85, 255, 255]` |
| Blue | `[100, 90, 90]` | `[130, 255, 255]` |
| Purple | `[130, 90, 90]` | `[160, 255, 255]` |
| Pink | `[160, 90, 140]` | `[179, 255, 255]` |

The shape filters:

| Field | What it restricts |
|---|---|
| `size` | Side of the target in pixels, from `min` to `max`. |
| `aspect` | Ratio between width and height. `1.0` is a square, `0.5` is twice as wide as tall. |
| `fill` | Fraction of the box filled with target pixels. A thin outline sits near `0.1`; a solid block sits near `1.0`. This is the filter that separates a ring from a rectangle. |
| `area_min` | Minimum area in pixels, to discard noise. |
| `work_scale` | Downscale applied before searching. `0.5` speeds things up a lot and still finds targets of 40 px or more. |

When more than one candidate passes the filters, the **largest** one wins.

### Tuning a profile

The loop is always the same: copy a profile, adjust `target`, test with `check --debug`, repeat. You never need to touch Python.

**Light and round target.** Copy `profiles/circulo_claro.json`. This is the most common case and it is ready as is.

**Dark target.** Replace `bright` with `dark`. `v_max` is the maximum brightness, so a black target on a light background uses something between `40` and `90`:

```json
"target": {
  "dark": { "v_max": 80, "s_max": 120 },
  "size": { "min": 45, "max": 240 },
  "aspect": { "min": 0.65, "max": 1.5 },
  "fill": { "min": 0.04, "max": 0.4 }
}
```

**Vivid colour.** A saturated pixel is neither `bright` nor `dark` unless the profile caps `s_max` low, and the code default of `255` caps nothing. Use an HSV range from the table above. Copy `profiles/faixa_hsv.json`, which already uses red, and swap the two triples. That profile also ships with `region.mode` set to `fixed` at `1920x1080`, so change it to `screen` unless you really do want a hard rectangle.

**Not round.** Adjust `aspect` and let `fill` accept the shape. A diamond or a triangle usually passes with `aspect` between `0.5` and `2.0` and `fill` from `0.2` to `0.6`. For a solid rectangle, raise the `fill` ceiling to `1.0`.

**A letter, number or icon.** Use the `template` detector instead. See [Detecting a letter or symbol](#detecting-a-letter-or-symbol).

### `pointer` — how the cursor moves

| `mode` | Behaviour |
|---|---|
| `teleport` | Goes straight to the centre. The default, and the fastest. |
| `smooth` | Follows a curved path, with tremor and irregular steps, like a hand. Use it when the destination program ignores instant movement. |

For `smooth` you can adjust `duration` (total movement time in seconds) and `jitter` (tremor amplitude, in pixels). `0.08` is fast, `0.30` is slow and discreet.

### `controls` — when to stop

| Field | Meaning |
|---|---|
| `corner_seconds` | How long the mouse must sit in the top-left corner to stop. Default `1.0`. |

**Esc** and **F12** always stop the loop, regardless of this field.

### When `shape` beats `template`

Use `shape` when the target is a **colour** and the shape does not matter much. It is faster and more stable, because it does not depend on an exact template or scale.

Use `template` when what identifies the target is the **shape or the text**, and the colour may vary.

---

## Detecting a letter or symbol

The `template` detector works with a reference image. The complete flow:

**1. Take a screenshot with the target visible**

```bash
python -m wolfs_screen_hitter capture screenshot.png
```

**2. Crop just the letter or symbol**

Use the coordinates from the screenshot. The command already prints the image size:

```bash
python -m wolfs_screen_hitter crop screenshot.png profiles/templates/target.png 640 300 48 52
```

That saves a `48x52` crop from that point. Keep the original, because that one is the screenshot, and the crop is the template.

**3. Point a profile at the template**

```json
{
  "name": "Target letter",
  "detector": "template",
  "window": { "title": null },
  "region": { "mode": "window", "margin": 0 },
  "target": {
    "template": "templates/target.png",
    "threshold": 0.8,
    "scale_min": 0.5,
    "scale_max": 2.0,
    "scale_steps": 12,
    "work_scale": 1.0,
    "invert": false
  },
  "pointer": { "mode": "teleport" }
}
```

The template path is relative to the profile file, so you can keep templates in `profiles/templates/`.

**4. Test before using it**

```bash
python -m wolfs_screen_hitter check profiles/letra_template.json --debug out/debug.png
```

### Tuning the template

| Field | Effect |
|---|---|
| `threshold` | Minimum similarity to accept, from 0 to 1. Start at `0.8`. Drop to `0.7` if it finds nothing. Raise to `0.9` if it keeps landing in the wrong place. |
| `scale_min` / `scale_max` | Range of sizes to test. If the target on screen is bigger or smaller than the crop, widen the range. |
| `scale_steps` | How many sizes are tested inside the range. More steps means more chance and more cost. |
| `work_scale` | Downscale for speed. At `0.5`, noise tolerance drops. |
| `invert` | Inverts the greyscale on both sides. Use it when the target is dark on a light background and `threshold` is not passing. |

### Reading the colour of your target

When you do not know what colour to put in the profile, let the tool measure it. Take a screenshot, crop a `1x1` pixel from the middle of the target, and read the value:

```bash
python -m wolfs_screen_hitter capture screenshot.png
python -m wolfs_screen_hitter crop screenshot.png hue.png 640 300 1 1
python -c "import cv2; print(cv2.cvtColor(cv2.imread('hue.png', cv2.IMREAD_COLOR), cv2.COLOR_BGR2HSV)[0][0])"
```

The output is the `[hue, saturation, value]` triple. Use it directly as `hsv_min`, and as `hsv_max` with the channels pushed up.

---

## Troubleshooting

Everything that commonly goes wrong, in one table. Find your symptom, read the cause, apply the fix.

### Detection

| Symptom | Cause | Fix |
|---|---|---|
| Finds nothing, but the target is right there | `work_scale` shrank the target below `size.min` | Raise it toward `1.0`. A low `work_scale` is for speed, not for small targets |
| Finds nothing | Target smaller than `size.min` | Lower `size.min` |
| Finds nothing | `bright`/`dark` do not match the colour | [Read the real value](#reading-the-colour-of-your-target) and match it |
| Finds nothing, target is a vivid colour | The profile caps saturation with `s_max`, so a saturated pixel is not `bright` or `dark` | Use `hsv_min`/`hsv_max` instead. The code default is `s_max` `255`, which accepts any saturation |
| Finds nothing, target is small or thin | Fill and size filters too strict | Widen `size`, loosen `aspect`, lower the `fill` floor |
| Box lands on a UI icon or button | Screen mode also sees your own interface | Use `region: "window"` with a `margin`, or `region: "fixed"` |
| Box lands on the wrong similar shape | Filters too loose | Lower the `fill` ceiling, tighten `aspect` |
| Picks the bigger false positive | The largest match always wins | Lower `size.max` below the real target's size |
| Target flickers, program seems to lose it | Detection runs on raw frames | Lower `work_scale` to `0.35` |
| Target looks like a rectangle, not a circle | `aspect` too narrow | Widen `aspect`, and raise the `fill` ceiling to `1.0` for a solid block |

### Location

| Symptom | Cause | Fix |
|---|---|---|
| Target disappears at random | Another window is on top of it | Bring it forward, or use `region: "window"` |
| Target found in several places | Only one result comes back: `shape` keeps the largest blob, `template` keeps the best match | Narrow the area with `region: "fixed"` |
| Window edges and bars get in the way | The search includes window chrome | Add `margin`, start at `0`, raise it while watching `--debug` |
| Wrong window is being searched | `title` does not match | Run `list-windows`. The match is case-insensitive and partial, so a distinctive fragment is enough |
| Prints `Aguardando a janela...` forever | The window is smaller than `window.min_width`/`min_height`, which both default to `200` | Lower them in the profile, or open the window bigger |
| Region came out empty | No window matched the title, or the rectangle is degenerate | Run `check` to see the resolved region, then fix `window.title` or `region` |
| Target is on a second monitor | `screen` only covers the primary | Use `region: "virtual"` |

### Movement

| Symptom | Cause | Fix |
|---|---|---|
| Cursor does not move at all | Nothing was detected | Run `check` first; if it finds nothing, fix detection |
| I move the mouse and it snaps back to the target | The loop re-centres the cursor on every frame, by design | Stop it with **Esc** or **F12**. No `pointer` setting yields control back to you; `smooth` only changes the path |
| Cursor too fast or too slow in `smooth` | `duration` and `jitter` | `duration` `0.08` fast, `0.30` slow; `jitter` is tremor in pixels |
| Cannot stop the loop | Not the usual keys | **Esc** or **F12**; or park the mouse in the top-left corner for `corner_seconds` |

### Templates

| Symptom | Cause | Fix |
|---|---|---|
| Template never matches | `threshold` is `0.80` by default and the match is just under it | Lower `threshold` towards `0.7`, and watch the score in `--debug` |
| Template never matches | The template is larger than the captured region, so every scale is skipped | Make the region bigger, or shrink the crop |
| Template never matches | Crop has extra background | Crop tightly to the glyph edges |
| Template never matches | Template background differs from the screen | Use `invert: true`, or remove the background from the crop |
| Template never matches | Target on screen is a different size | Widen `scale_min`/`scale_max`, raise `scale_steps` |
| Word not recognised as one target | The detector looks for a single image | One template and one profile per letter or symbol |
| Template is slow | Too many scales on a large region | Lower `work_scale` to `0.5` or `0.35` |

### Performance and install

| Symptom | Cause | Fix |
|---|---|---|
| Slow on a large monitor | Too many pixels to search | Lower `work_scale` to `0.35`, or use `window` with a margin |
| A stack trace ends in `ProfileError` | The profile is missing a field, has the wrong type, or names an unknown detector or `pointer.mode` | Read the last line: it names the field. Compare against a shipped profile |
| `JSON invalido ... Unexpected UTF-8 BOM` | The file was saved with a byte order mark, which `json` refuses | Save as UTF-8 without BOM. In PowerShell that is `-Encoding utf8NoBOM`, not `-Encoding UTF8` |
| `ModuleNotFoundError` | Dependencies missing, or wrong folder | `pip install -r requirements.txt`, then run from the project folder |
| `wolfs-screen-hitter` command not found | Package not installed | `pip install -e .`, or use `python -m wolfs_screen_hitter` |
| Capture is slow or fails | DXGI unavailable | It falls back to `mss` automatically; if both fail, check the screen is not locked |

---

## Tests

Two scripts, no extra framework. Neither one touches your mouse by default: the parts that move the cursor are opt-in.

```bash
python tests/test_local.py
```

Safe to run at any time. Checks offline that the package contains no click calls, that `pyautogui` is not a dependency, that the profiles load, and that detectors, regions and movement modes behave. Finishes on its own, one line per check.

```bash
python tests/test_local.py --executar
python tests/test_e2e.py --executar
```

These move your mouse and focus a window for a few seconds, so they do nothing without the flag. With it, `test_local.py` adds the two real movement checks, and `test_e2e.py` builds a scene with a light ring and a red ring, opens it in the Windows viewer, captures the real screen over DXGI, confirms it detected the light ring and ignored the red one, and moves the cursor to the centre of the target.

Without the flag those checks show up as `[skipped]` and everything else is still verified. Use `--executar` when you are not typing, because the cursor will jump around the screen.

Two more scripts keep this documentation honest. They need no mouse and no screen:

```bash
python tests/test_readme.py
python tests/test_readme_citacoes.py
```

The first checks that both READMEs have the same structure, that every internal link resolves, and that setup is the first section. The second checks that every command, flag, file, profile key and enum value cited in the READMEs actually exists in the code. If you change the code and forget the docs, these fail.

---

## Privacy

Everything runs locally. No information leaves your machine, and the capture is restricted to the region you configured in the profile.

## License

MIT. See [LICENSE](LICENSE).
