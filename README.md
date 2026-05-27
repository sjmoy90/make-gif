# make_gif

Command-line utility to build an animated GIF from a sequence of images.

## Requirements

- Python 3.12+
- Pillow 10+

```bash
pip install -r requirements.txt
```

---

## Quick start

```bash
python3 make_gif.py --folder samples --fps 2 --out animation.gif
```

The `samples/` directory contains five CC0-licensed photos from [Lorem Picsum](https://picsum.photos) (800×600 px each).

---

## A worked example

```bash
python3 make_gif.py \
  img_001.jpeg img_002.jpeg img_003.jpeg img_004.jpeg img_005.jpeg img_final.jpeg \
  --duration 1 --last-duration 3 \
  --bg linen \
  --target-mb 4.0 \
  --out animation.gif
```

| Flag | What it does here |
|---|---|
| `img_001.jpeg … img_final.jpeg` | Six frames, in this order |
| `--duration 1` | Each frame shows for 1 second… |
| `--last-duration 3` | …except the last, which stays for 3 seconds |
| `--bg linen` | `img_final.jpeg` is portrait; the script fits it inside the landscape canvas and fills the empty sides with linen |
| `--target-mb 4.0` | Binary-searches for the largest resolution that keeps the file under 4 MB |
| `--out animation.gif` | Output filename |

---

## Specifying frames

You have three ways to specify input images — they can be combined, and are always applied in this order: folder → glob → explicit files.

**From a folder** — loads every supported image in the directory, sorted by filename:
```bash
python3 make_gif.py --folder shots --fps 4 --out animation.gif
```

If your filenames aren't meaningful, sort by timestamp instead:
```bash
python3 make_gif.py --folder shots --sort mtime --fps 4 --out animation.gif
python3 make_gif.py --folder shots --sort ctime --fps 4 --out animation.gif
```
`ctime` uses file creation time on macOS; falls back to last-modified on Linux.

**By glob pattern** — sorted alphabetically:
```bash
python3 make_gif.py --glob "frame_*.jpeg" --fps 4 --out animation.gif
```

**Explicit files** — in exactly the order you type them:
```bash
python3 make_gif.py intro.jpeg slide1.jpeg slide2.jpeg outro.jpeg --out animation.gif
```

---

## Timing

All frames the same speed:
```bash
--fps 4            # 4 frames per second
--duration 0.5     # 0.5 seconds per frame (same thing)
```

Hold the last frame longer:
```bash
--duration 1 --last-duration 5
```

Full control per frame (count must match number of frames):
```bash
--durations 0.5 0.5 0.5 3
```

---

## Sizing

Let the script find the right resolution automatically:
```bash
--target-mb 4.0    # binary-searches for the largest width under 4 MB
```

Or set a fixed width (height is scaled proportionally):
```bash
--width 1200
```

---

## Mixed aspect ratios

When frames have different aspect ratios, each frame is scaled to fit inside the first frame's canvas, and the empty space is filled with `--bg` (default: white). Any CSS color name or hex code works; unrecognized values fall back to white with a warning.

```bash
--bg linen
--bg "#2b2b2b"
--bg black
```

---

## All options

```
python3 make_gif.py [options] [image ...]
```

| Flag | Default | Description |
|---|---|---|
| `--folder DIR`, `-f` | — | Load all images from a directory |
| `--sort name\|mtime\|ctime` | `name` | Sort order for `--folder` |
| `--glob PATTERN`, `-g` | — | Glob pattern (sorted alphabetically) |
| `--out PATH`, `-o` | `animation.gif` | Output file |
| `--fps N` | — | Uniform frame rate |
| `--duration SEC` | `1.0` | Uniform frame duration in seconds |
| `--last-duration SEC` | — | Override the last frame's duration |
| `--durations S1 S2 …` | — | Per-frame durations (must match frame count) |
| `--target-mb N` | — | Auto-resize to stay under N MB |
| `--width N` | — | Fixed output width (height auto-scaled) |
| `--bg COLOR` | `white` | Padding color for aspect-ratio mismatches |
| `--loop N`, `-l` | `0` | Loop count; 0 = loop forever |
| `--no-resize` | off | Skip padding/resizing frames |

---

Developed and tested on macOS · Python 3.12.12 · Pillow 12.1.1
