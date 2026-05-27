# make_gif

A command-line utility to build an animated GIF from a sequence of images, with support for per-frame timing, aspect-ratio-safe padding, and automatic resolution scaling to hit a target file size.

## Requirements

- Python 3.12+
- Pillow 10+

```bash
pip install -r requirements.txt
```

## Usage

```
python3 make_gif.py [options] <image1> <image2> ...
python3 make_gif.py [options] --glob "*.jpeg"
```

## Examples

**Basic — uniform 1 s per frame:**
```bash
python3 make_gif.py img_001.jpeg img_002.jpeg img_003.jpeg --out animation.gif
```

**Last frame held longer (1 s each, final frame 3 s):**
```bash
python3 make_gif.py img_001.jpeg img_002.jpeg img_003.jpeg img_final.jpeg \
  --duration 1 --last-duration 3 --out animation.gif
```

**Explicit per-frame durations:**
```bash
python3 make_gif.py img_001.jpeg img_002.jpeg img_final.jpeg \
  --durations 0.5 0.5 3 --out animation.gif
```

**Glob input, 4 fps:**
```bash
python3 make_gif.py --glob "img_*.jpeg" --fps 4 --out animation.gif
```

**Automatically resize to stay under a target file size:**
```bash
python3 make_gif.py img_001.jpeg img_002.jpeg img_final.jpeg \
  --duration 1 --last-duration 3 --target-mb 4.5 --out animation.gif
```

**Set an explicit output width (height auto-scaled):**
```bash
python3 make_gif.py --glob "img_*.jpeg" --width 1200 --out animation.gif
```

**Custom padding color for mixed-aspect-ratio frames:**
```bash
python3 make_gif.py img_001.jpeg img_final.jpeg \
  --duration 1 --last-duration 3 --bg black --out animation.gif
```

## Options

| Flag | Default | Description |
|---|---|---|
| `--out`, `-o` | `animation.gif` | Output file path |
| `--duration` | `1.0` | Uniform frame duration in seconds |
| `--last-duration` | — | Override duration for the last frame |
| `--durations S1 S2 …` | — | Explicit per-frame durations (must match frame count) |
| `--fps` | — | Uniform timing via frames-per-second (overrides `--duration`) |
| `--glob`, `-g` | — | Collect frames via a glob pattern (sorted) |
| `--width` | — | Scale all frames to this width; height auto-scaled |
| `--target-mb` | — | Binary-search for the largest width under this file size (MB) |
| `--bg` | `white` | Padding color for frames with a different aspect ratio (any CSS color name or hex); falls back to white if invalid |
| `--loop`, `-l` | `0` | Loop count; `0` = loop forever |
| `--no-resize` | off | Skip resizing frames to match the first frame's dimensions |

## Notes

- When frames have different aspect ratios, the script letterboxes smaller frames onto a canvas matching the first frame's dimensions, padding with `--bg`.
- `--target-mb` runs up to 12 binary-search iterations and prints the size at each step.
- Developed and tested on macOS with Python 3.12.12 and Pillow 12.1.1.
