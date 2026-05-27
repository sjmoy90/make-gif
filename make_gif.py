#!/usr/bin/env python3
"""
make_gif.py — build an animated GIF from a sequence of images.

Frame sources (applied in this order, combined into one list):
  --folder DIR    all supported images in DIR, ordered by --sort
  --glob PATTERN  files matching a glob pattern, ordered alphabetically
  positional args explicit files, in the order given

Timing:
  --duration SEC          uniform frame duration (default 1 s)
  --last-duration SEC     override the last frame's duration
  --durations S1 S2 ...   explicit per-frame durations
  --fps N                 uniform timing via frames-per-second

Sizing:
  --width N       scale all frames to this width (height auto-scaled)
  --target-mb N   binary-search for the largest width under N MB

Examples:
    # All images in a folder at 2 fps:
    python3 make_gif.py --folder samples --fps 2 --out animation.gif

    # Folder sorted by last-modified time:
    python3 make_gif.py --folder shots --sort mtime --fps 4 --out animation.gif

    # 1 s each, last frame 3 s, auto-resize to stay under 4.5 MB:
    python3 make_gif.py img_001.jpeg img_002.jpeg img_final.jpeg \
        --duration 1 --last-duration 3 --target-mb 4.5 --out animation.gif
"""

import argparse
import glob as glob_module
import io
import sys
from pathlib import Path

from PIL import Image, ImageColor

IMAGE_EXTS = {".jpeg", ".jpg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def resolve_color(color: str, default: str = "white") -> str:
    try:
        ImageColor.getrgb(color)
        return color
    except (ValueError, AttributeError):
        print(f"Warning: unrecognized color {color!r}, defaulting to {default!r}.")
        return default


def _sort_key(p: Path, sort: str):
    if sort == "mtime":
        return p.stat().st_mtime
    if sort == "ctime":
        st = p.stat()
        # st_birthtime is macOS/BSD; fall back to st_mtime on Linux
        return getattr(st, "st_birthtime", st.st_mtime)
    return p.name  # default: alphabetical by filename


def collect_folder(folder: Path, sort: str) -> list[str]:
    images = [p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTS]
    images.sort(key=lambda p: _sort_key(p, sort))
    return [str(p) for p in images]


def load_images(paths: list[str]) -> list[Image.Image]:
    return [Image.open(p).convert("RGBA") for p in paths]


def fit_with_padding(img: Image.Image, target: tuple[int, int], bg: str = "white") -> Image.Image:
    """Scale img to fit within target preserving aspect ratio, padding remainder with bg."""
    img.thumbnail(target, Image.LANCZOS)
    canvas = Image.new("RGBA", target, bg)
    x = (target[0] - img.width) // 2
    y = (target[1] - img.height) // 2
    canvas.paste(img, (x, y))
    return canvas


def scale_frames(frames: list[Image.Image], width: int) -> list[Image.Image]:
    orig_w, orig_h = frames[0].size
    if orig_w == width:
        return frames
    ratio = width / orig_w
    new_size = (width, max(1, int(orig_h * ratio)))
    return [f.resize(new_size, Image.LANCZOS) for f in frames]


def resize_to_first(frames: list[Image.Image], bg: str = "white") -> list[Image.Image]:
    target = frames[0].size
    resized = [frames[0]]
    for f in frames[1:]:
        if f.size != target:
            f = fit_with_padding(f, target, bg=bg)
        resized.append(f)
    return resized


def encode_gif(frames: list[Image.Image], durations_ms: list[int], loop: int) -> bytes:
    first = frames[0].convert("P", palette=Image.ADAPTIVE, colors=256)
    rest = [f.convert("P", palette=Image.ADAPTIVE, colors=256) for f in frames[1:]]
    buf = io.BytesIO()
    first.save(
        buf,
        format="GIF",
        save_all=True,
        append_images=rest,
        duration=durations_ms,
        loop=loop,
        optimize=False,
    )
    return buf.getvalue()


def make_gif(
    paths: list[str],
    out: str,
    durations_ms: list[int],
    loop: int = 0,
    resize: bool = True,
    bg: str = "white",
    width: int | None = None,
    target_mb: float | None = None,
) -> None:
    if not paths:
        raise ValueError("No input images provided.")
    if len(durations_ms) != len(paths):
        raise ValueError(
            f"Duration list length ({len(durations_ms)}) must match frame count ({len(paths)})."
        )

    print(f"Loading {len(paths)} frame(s)…")
    frames = load_images(paths)

    if resize and len(frames) > 1:
        frames = resize_to_first(frames, bg=bg)

    orig_width = frames[0].width

    if target_mb is not None:
        target_bytes = int(target_mb * 1024 * 1024)
        lo, hi = 100, orig_width
        best_width = hi
        best_data = None

        print(f"Binary-searching for width that fits under {target_mb} MB…")
        for _ in range(12):  # 12 iterations → width precision < 0.05%
            mid = (lo + hi) // 2
            candidate = encode_gif(scale_frames(frames, mid), durations_ms, loop)
            size_mb = len(candidate) / 1024 / 1024
            print(f"  width={mid}  →  {size_mb:.2f} MB")
            if len(candidate) <= target_bytes:
                best_width = mid
                best_data = candidate
                lo = mid + 1
            else:
                hi = mid - 1

        if best_data is None:
            print("Warning: could not reach target size even at minimum width; using smallest tried.", file=sys.stderr)
            best_data = encode_gif(scale_frames(frames, 100), durations_ms, loop)

        out_path = Path(out)
        out_path.write_bytes(best_data)
        final_mb = len(best_data) / 1024 / 1024
        print(f"Saved {out_path}  (width={best_width}, {final_mb:.2f} MB)")

    else:
        if width is not None:
            frames = scale_frames(frames, width)

        data = encode_gif(frames, durations_ms, loop)
        out_path = Path(out)
        out_path.write_bytes(data)
        size_mb = len(data) / 1024 / 1024
        total_s = sum(durations_ms) / 1000
        print(f"Saved {out_path}  ({len(frames)} frames, {total_s:.1f}s total, {size_mb:.2f} MB)")


def resolve_durations(
    n: int,
    duration: float,
    last_duration: float | None,
    durations: list[float] | None,
) -> list[int]:
    if durations is not None:
        if len(durations) != n:
            raise ValueError(
                f"--durations has {len(durations)} values but there are {n} frames."
            )
        return [int(d * 1000) for d in durations]

    ms = [int(duration * 1000)] * n
    if last_duration is not None:
        ms[-1] = int(last_duration * 1000)
    return ms


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build an animated GIF from images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("images", nargs="*", help="Input image files (used as-is, in the order given)")
    parser.add_argument("--folder", "-f", metavar="DIR",
                        help="Load all supported images from DIR; order controlled by --sort")
    parser.add_argument("--sort", choices=["name", "mtime", "ctime"], default="name",
                        help="Sort order for --folder images: "
                             "name=alphabetical by filename (default), "
                             "mtime=last modified, "
                             "ctime=creation time (macOS/BSD; falls back to mtime on Linux)")
    parser.add_argument("--glob", "-g", metavar="PATTERN",
                        help='Glob pattern for frames, e.g. "img_*.jpeg" (sorted alphabetically)')
    parser.add_argument("--out", "-o", default="animation.gif", help="Output path (default: animation.gif)")
    parser.add_argument("--loop", "-l", type=int, default=0, help="Loop count; 0 = loop forever (default: 0)")
    parser.add_argument("--no-resize", action="store_true",
                        help="Skip padding/resizing frames to match the first frame's dimensions")
    parser.add_argument("--bg", default="white",
                        help="Padding color for frames with a different aspect ratio "
                             "(CSS color name or hex, default: white; falls back to white if invalid)")

    timing = parser.add_mutually_exclusive_group()
    timing.add_argument("--fps", type=float, help="Uniform frame rate (frames per second)")
    timing.add_argument("--durations", type=float, nargs="+", metavar="SEC",
                        help="Per-frame durations in seconds (count must match total frames)")

    parser.add_argument("--duration", type=float, default=1.0,
                        help="Uniform frame duration in seconds (default: 1.0); "
                             "ignored when --fps or --durations is set")
    parser.add_argument("--last-duration", type=float, dest="last_duration",
                        help="Override duration for the last frame (seconds)")

    sizing = parser.add_mutually_exclusive_group()
    sizing.add_argument("--width", type=int, help="Scale all frames to this width (height auto-scaled)")
    sizing.add_argument("--target-mb", type=float, dest="target_mb",
                        help="Binary-search for the largest width that keeps the GIF under this size in MB")

    args = parser.parse_args()

    paths: list[str] = []

    if args.folder:
        folder = Path(args.folder)
        if not folder.is_dir():
            print(f"Error: {args.folder!r} is not a directory.", file=sys.stderr)
            sys.exit(1)
        folder_paths = collect_folder(folder, args.sort)
        if not folder_paths:
            print(f"No supported image files found in {args.folder!r}.", file=sys.stderr)
            sys.exit(1)
        print(f"Found {len(folder_paths)} image(s) in {args.folder!r} (sorted by {args.sort}):")
        for p in folder_paths:
            print(f"  {Path(p).name}")
        paths.extend(folder_paths)

    if args.glob:
        matched = sorted(glob_module.glob(args.glob))
        if not matched:
            print(f"No files matched: {args.glob}", file=sys.stderr)
            sys.exit(1)
        paths.extend(matched)

    paths.extend(args.images)

    if not paths:
        parser.print_help()
        sys.exit(1)

    if args.fps:
        base_duration = 1.0 / args.fps
    else:
        base_duration = args.duration

    try:
        durations_ms = resolve_durations(
            n=len(paths),
            duration=base_duration,
            last_duration=args.last_duration,
            durations=args.durations,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    make_gif(
        paths,
        args.out,
        durations_ms=durations_ms,
        loop=args.loop,
        resize=not args.no_resize,
        bg=resolve_color(args.bg),
        width=args.width,
        target_mb=args.target_mb,
    )


if __name__ == "__main__":
    main()
