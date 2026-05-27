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
python3 make_gif.py [options] [image1 image2 ...]
```

Frame sources are combined in this order: `--folder` → `--glob` → positional arguments.

## Sample images

The `samples/` directory contains five CC0-licensed photos from [Lorem Picsum](https://picsum.photos) (800×600 px each), ready to use for testing:

```bash
python3 make_gif.py --folder samples --fps 2 --out animation.gif
```

## Examples

**All images in a folder (sorted by filename):**
```bash
python3 make_gif.py --folder samples --fps 2 --out animation.gif
```

**Folder sorted by last-modified time:**
```bash
python3 make_gif.py --folder shots --sort mtime --fps 4 --out animation.gif
```

**Folder sorted by creation time:**
```bash
python3 make_gif.py --folder shots --sort ctime --fps 4 --out animation.gif
```

**Glob pattern:**
```bash
python3 make_gif.py --glob "img_*.jpeg" --fps 4 --out animation.gif
```

**Explicit files, 1 s each, last frame held for 3 s:**
```bash
python3 make_gif.py img_001.jpeg img_002.jpeg img_final.jpeg \
  --duration 1 --last-duration 3 --out animation.gif
```

**Explicit per-frame durations:**
```bash
python3 make_gif.py img_001.jpeg img_002.jpeg img_final.jpeg \
  --durations 0.5 0.5 3 --out animation.gif
```

**Automatically resize to stay under a target file size:**
```bash
python3 make_gif.py --folder samples \
  --duration 1 --target-mb 4.5 --out animation.gif
```

**Set an explicit output width (height auto-scaled):**
```bash
python3 make_gif.py --folder samples --width 1200 --out animation.gif
```

**Custom padding color for mixed-aspect-ratio frames:**
```bash
python3 make_gif.py img_001.jpeg img_final.jpeg \
  --duration 1 --last-duration 3 --bg black --out animation.gif
```

## Options

### Frame sources

| Flag | Description |
|---|---|
| `positional` | Explicit image files, used in the order given |
| `--folder DIR`, `-f` | Load all supported images from a directory; order set by `--sort` |
| `--sort` | Sort order for `--folder`: `name` (alphabetical by filename, default), `mtime` (last modified), `ctime` (creation time — macOS/BSD only; falls back to `mtime` on Linux) |
| `--glob PATTERN`, `-g` | Glob pattern (sorted alphabetically by filename) |

If images in a folder have arbitrary filenames, use `--sort mtime` or `--sort ctime` to order them by timestamp rather than name.

### Timing

| Flag | Default | Description |
|---|---|---|
| `--duration SEC` | `1.0` | Uniform frame duration in seconds |
| `--last-duration SEC` | — | Override duration for the last frame |
| `--durations S1 S2 …` | — | Explicit per-frame durations (count must match total frames) |
| `--fps N` | — | Uniform timing via frames-per-second (overrides `--duration`) |

### Sizing

| Flag | Description |
|---|---|
| `--width N` | Scale all frames to this width; height auto-scaled |
| `--target-mb N` | Binary-search for the largest width that keeps the GIF under N MB |

### Output

| Flag | Default | Description |
|---|---|---|
| `--out PATH`, `-o` | `animation.gif` | Output file path |
| `--loop N`, `-l` | `0` | Loop count; `0` = loop forever |
| `--bg COLOR` | `white` | Padding color for frames with a different aspect ratio (CSS color name or hex; falls back to white if unrecognized) |
| `--no-resize` | off | Skip padding/resizing frames to match the first frame's dimensions |

## Notes

- When frames have different aspect ratios, the script letterboxes them onto a canvas matching the first frame's dimensions, padding with `--bg`.
- `--target-mb` runs up to 12 binary-search iterations and prints the size at each step.
- Developed and tested on macOS with Python 3.12.12 and Pillow 12.1.1.
