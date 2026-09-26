# WolfsScreenHitter

[English](README.md) | [Português](README.pt.md)

Points your mouse cursor at a **visual target on screen**, found in real time by colour or by a reference image. The click is always yours: the program only positions the cursor, it never clicks.

Two ways to recognise the target, both configured through a JSON file:

- **`shape`** — finds blobs of a colour whose shape is close to a circle. Good for coloured targets, outlines, buttons, indicators.
- **`template`** — locates the image of a letter, symbol, icon or number using multi-scale template matching. Good for reading text on screen.

Runs on Windows, with the target anywhere you choose: a specific window, the central area of that window, the whole screen, the virtual desktop, or a fixed rectangle.

## Tests

Two scripts, no extra framework. Neither one touches your mouse by default: the parts that move the cursor are opt-in.

The first is safe to run at any time:

```bash
python tests/test_local.py
```

It checks offline that the package contains no click calls, that `pyautogui` is not a dependency, that the profiles load, and that detectors, regions and movement modes behave. It finishes on its own, printing one line per check.

The second one moves your mouse and focuses a window for a few seconds, so it does nothing without the flag:

```bash
python tests/test_e2e.py --executar
```

This is the real test: it builds a scene with a light ring and a red ring, opens it in the Windows viewer, captures the real screen over DXGI, confirms it detected the light ring and ignored the red one, and moves the cursor to the centre of the target.

The two movement checks in `test_local.py` are opt-in as well:

```bash
python tests/test_local.py --executar
```

Without the flag they show up as `[skipped]`, and everything else is still verified. Use `--executar` when you are not typing, because the cursor will jump around the screen.

## What this program does not do

- It does not click. There is no button call anywhere in the code, and a test enforces that.
- It does not type anything.
- It does not send network events, and it reads nothing outside the area you configured.

If you need automatic clicking, this is the wrong project.

## Installation

Requires Python 3.10 or newer.

```bash
git clone https://github.com/IsmarWolf/WolfsScreenHitter.git
cd WolfsScreenHitter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Optionally, to get the `wolfs-screen-hitter` command available:

```bash
pip install -e .
```

## Quick start

```bash
# see what is available
python -m wolfs_screen_hitter list-profiles
python -m wolfs_screen_hitter list-windows

# test the detection without touching the mouse (always start here)
python -m wolfs_screen_hitter check profiles/circulo_claro.json --debug out/debug.png

# follow the target for real
python -m wolfs_screen_hitter run profiles/circulo_claro.json
```

Stop with **Esc**, **F12**, or by leaving the mouse parked in the top-left corner for a second.

The `check` command is the most useful one when tuning a profile: it tells you whether it found anything, where it is, and saves an image with the box drawn on it so you can see what the detector saw.

## It works on any screen

The program does not know, and does not need to know, which program is your target. It does not look for a game name or a specific window unless you ask it to. By default the `circulo_claro.json` profile sweeps the whole screen and recognises the target by shape and colour.

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

### The difference that matters: window or whole screen

Choosing `screen` is the easiest and most broad, but it has a consequence: the detector sees **everything that is visible**, including the interface of your own programs. If you have a light round icon in the corner of the screen, it is just as valid a candidate as the real target, and the detector will pick the largest one.

When that happens, narrow the search. `margin` is the right tool: it erases a band around the window, discarding the icons, buttons and status bars that sit near the edges.

How to find the right margin for your case: start at `0`, run `check` with `--debug`, and look at where the green box landed. If it landed on an edge icon, raise the margin until that icon is cut off. If the box disappeared along with the target, lower it.

To find the exact window title, run `list-windows` and copy the name that shows up.

### One detail about what is visible

The detector works on what the screen camera sees, which is what is **drawn on screen**. If another window is on top of the target, the target does not exist as far as the detector is concerned. This is not a defect: it is what any screen capture does.

If you use the `screen` mode and the target vanishes for no reason, it is usually because your browser, terminal or editor came to the front. In that case `window` is the right mode.

## Tuning a profile for your target

The flow is always the same: copy one of the example profiles, adjust the `target`, test with `check` looking at the `--debug` image, repeat. You never need to touch Python.

### If the target is light and round

Copy `profiles/circulo_claro.json`. This is the most common case and it is ready as is.

### If the target is dark

Replace `bright` with `dark`. `v_max` is the maximum brightness, so a black target on a light background uses something between `40` and `90`:

```json
"target": {
  "dark": { "v_max": 80, "s_max": 120 },
  "size": { "min": 45, "max": 240 },
  "aspect": { "min": 0.65, "max": 1.5 },
  "fill": { "min": 0.04, "max": 0.4 }
}
```

### If the target has a vivid colour

Strong colours are rejected by `bright` and by `dark` because they are highly saturated. Use an HSV range instead. The values are `[hue, saturation, value]`, and hue runs from 0 to 179 in OpenCV:

| Colour | `hsv_min` | `hsv_max` |
|---|---|---|
| Red | `[0, 140, 140]` | `[10, 255, 255]` |
| Orange/yellow | `[11, 140, 140]` | `[30, 255, 255]` |
| Green | `[35, 90, 90]` | `[85, 255, 255]` |
| Blue | `[100, 90, 90]` | `[130, 255, 255]` |
| Purple | `[130, 90, 90]` | `[160, 255, 255]` |
| Pink | `[160, 90, 140]` | `[179, 255, 255]` |

Copy `profiles/faixa_hsv.json`, which already uses red, and swap the two triples.

To find the hue of a pixel, use a screenshot the program itself took:

```bash
python -m wolfs_screen_hitter capture screenshot.png
python -m wolfs_screen_hitter crop screenshot.png hue.png 640 300 1 1
```

That is a `1x1` crop of a point on the target. Then read the HSV triple with Python:

```bash
python -c "import cv2; print(cv2.cvtColor(cv2.imread('hue.png', cv2.IMREAD_COLOR), cv2.COLOR_BGR2HSV)[0][0])"
```

### If the target is not round

Adjust `aspect` and let `fill` accept the shape. A diamond or a triangle usually passes with `aspect` between `0.5` and `2.0` and `fill` from `0.2` to `0.6`. If it is a solid rectangle, raise the `fill` ceiling to `1.0`.

### If the target is a letter, number or icon

Use the `template` detector instead of `shape`. The complete walkthrough is in [Detecting a letter or symbol](#detecting-a-letter-or-symbol).

## Recipes for common problems

These are the adjustments that fix almost everything. Always start by testing with `check --debug` before changing any number.

**It finds nothing, and I know the target is on screen**

Almost always the `work_scale` is removing the target. If the target is smaller than about 40 px, drop it to `0.35` or set `1.0`. If the target is small by nature, lower `size.min` as well.

**It finds something, but the box lands in the wrong place**

Lower the `fill` ceiling to discard solid blocks, or raise the `aspect` limits to discard bars and strips. If the real target is smaller than the false positive, remember the detector picks the largest by default, so tighten `size.max`.

**It picks up an icon or a UI button**

Do not touch `target`, touch `region`. Use `mode: "window"` with a `margin`, or `mode: "fixed"` to limit the area.

**It finds the target but the cursor does not go there**

The destination program is ignoring instant movement. Switch `"mode": "teleport"` to `"mode": "smooth"`.

**The target flickers and the program seems to lose it**

Normal. The loop only acts when there is a detection. To smooth it out, reduce `work_scale` to `0.35`: a smaller image means less noise and a better chance of hitting on intermediate frames.

**The target window has edges or bars in the way**

Use `margin`. Start at `0` and raise it little by little, checking the `--debug` image at each step.

**It is slow on a large monitor**

Drop `work_scale` to `0.35`, or switch `screen` to `window` with a margin, which captures far fewer pixels.

**I want the cursor faster or slower in `smooth` mode**

`duration` is the total movement time in seconds. `0.08` is fast, `0.30` is slow and discreet. `jitter` is the tremor amplitude, in pixels.

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

| `mode` | Meaning |
|---|---|
| `window` | The area of the `window.title` window. Use `margin` to discard the edges. |
| `screen` | The entire primary screen. |
| `virtual` | All monitors together. |
| `fixed` | A fixed rectangle, with `left`, `top`, `width`, `height`. |

`margin` is the most useful trick: many programs draw icons near the edges, and `margin: 130` takes them out of consideration.

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

picks an exact range of hue, saturation and value. `hsv_min` and `hsv_max` replace `bright`/`dark` when present. Useful for a specific colour, for instance vivid red: hue from 0 to 12.

The shape filters:

| Field | What it restricts |
|---|---|
| `size` | Side of the target in pixels, from `min` to `max`. |
| `aspect` | Ratio between width and height. `1.0` is a square, `0.5` is twice as wide as tall. |
| `fill` | Fraction of the box filled with target pixels. A thin outline sits near `0.1`; a solid block sits near `1.0`. This is the filter that separates a ring from a rectangle. |
| `area_min` | Minimum area in pixels, to discard noise. |
| `work_scale` | Downscale applied to the image before searching. `0.5` speeds things up a lot and still finds targets of 40 px or more. |

When more than one candidate passes the filters, the **largest** one wins.

### `pointer` — how the cursor moves

| `mode` | Behaviour |
|---|---|
| `teleport` | Goes straight to the centre. This is the default and the fastest. |
| `smooth` | Follows a curved path, with tremor and irregular steps, like a hand. Use it when the destination program ignores instant movement. |

For `smooth` you can adjust `duration` (in seconds) and `jitter` (tremor amplitude, in pixels).

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

### Tips for templates that do not work

- **Crop tightly.** Leftover background in the template makes the match worse. Go right up to the glyph edges.
- **Background similar to the screen.** If the template has a white background and the screen is dark, use `invert: true` or remove the background from the crop.
- **Scale matters.** If the target on screen is twice the size of the crop, set `scale_min: 1.5`.
- **Words are not a single target.** Make one template per letter or symbol, and one profile for each. The detector always returns the best match for the image you gave it.
- **Several identical targets on screen.** The detector always returns the highest score. If you need one specific target, narrow the search area with `region.fixed`.

## When `shape` beats `template`

Use `shape` when the target is a **colour** and the shape does not matter much. It is faster and more stable, because it does not depend on an exact template or scale.

Use `template` when what identifies the target is the **shape or the text**, and the colour may vary.

## Troubleshooting

**`check` says it found nothing**

Save the debug image and look at what the detector saw:

```bash
python -m wolfs_screen_hitter check profiles/mine.json --debug out/debug.png
```

If the green box does not appear, the target did not pass the filters. Widen `size`, loosen `aspect`, raise `fill`, and check that `bright`/`dark` describe the colour well.

**It found the wrong place**

Usually it is a similar-looking interface element. Restrict the region with `region.margin`, or lower `fill` if the real target is thinner than the false positive.

**The cursor does not move**

Check the `list-windows` output and the `title` in your profile. Titles only need to match partially: `"title": "Paint"` finds `"Paint - picture.png"`.

**The target appears in several places**

`template` always returns the best score. Close the search area down with `region.fixed` to isolate it.

**It is slow**

Raise `work_scale` to `0.35` in the `shape` profile, or lower `scale_steps` in the `template` one. DXGI capture is fast; the cost is in the detection.

**The target program ignores the cursor movement**

Switch `"mode": "teleport"` to `"mode": "smooth"`. Some programs only register chained movement events.

## Privacy

Everything runs locally. No information leaves your machine, and the capture is restricted to the region you configured in the profile.

## License

MIT. See [LICENSE](LICENSE).
