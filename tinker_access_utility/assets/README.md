# Tray icon assets

- `taicon.png` — source artwork (172×350 RGBA), used directly on Windows and Linux tray icons.
- `taicon-template.png` — derived monochrome variant for the macOS menu bar, used as an
  [NSImage template](https://developer.apple.com/documentation/appkit/nsimage/1520017-template).
  RGB is `(0,0,0)` everywhere and alpha encodes the figure's luminance, so the
  system tints it correctly in light/dark mode and on hover.
- `taicon-app.png` — square 1024×1024 derivation of `taicon.png`, padded with
  transparency. Source for the macOS `.app` icon (Dock, Finder, Launchpad). Built
  at release time into a `.icns` by `scripts/build-macos-app.sh`. **Not** the
  menu-bar icon — that's still `taicon-template.png`.

`taicon.png` and `taicon-template.png` are loaded via `include_bytes!` in
`src/applet/tray.rs`; selection between them is a compile-time
`#[cfg(target_os = "macos")]`. `taicon-app.png` is consumed only by the macOS
release pipeline.

## Regenerating `taicon-app.png`

Pad the source to a square canvas at the largest icon size macOS expects (1024×1024):

```sh
magick taicon.png -background none -gravity center \
  -resize 896x896 -extent 1024x1024 \
  PNG32:taicon-app.png
```

`-resize 896x896` fits the figure inside ~87.5% of the canvas (Apple's
recommended safe area for macOS icons), `-extent 1024x1024` centers it on a
transparent square, and `-background none` keeps the padding transparent.

Replace this file with a designed-for-purpose square icon at any time — the
rest of the pipeline doesn't care how it was produced, only that it's a square
RGBA PNG ≥ 512×512.

## Regenerating `taicon-template.png`

The template is a *luminance-as-alpha* conversion of `taicon.png`: darker
source pixels become more opaque black, lighter ones fade out. This preserves
the line-art feel including the "TA" lettering at small sizes.

Run from this directory with ImageMagick 7+:

```sh
magick taicon.png \
  \( +clone -alpha extract \) \
  \( -clone 0 -alpha off -colorspace Gray -negate \) \
  -delete 0 \
  -compose Multiply -composite \
  -alpha copy \
  -background black -alpha shape \
  PNG32:taicon-template.png
```

Pipeline, top to bottom:

1. Extract the source alpha as a grayscale mask.
2. Take a second copy, drop alpha, convert to grayscale, and negate so dark
   source pixels become bright (high values).
3. Discard the original RGBA so only the two masks remain on the stack.
4. Multiply them — pixels need to be both inside the figure *and* dark in the
   source to end up opaque.
5. Copy the resulting grayscale into the alpha channel.
6. `-background black -alpha shape` rebuilds the image with a solid black RGB
   layer and the computed alpha, then `PNG32:` forces full RGBA output.

## Alternative: pure silhouette

If the luminance variant looks too noisy at the menu-bar size you actually
ship, swap step 2 for a flat fill — every visible pixel becomes fully opaque
black, giving a clean silhouette of the figure (loses the "TA" lettering and
internal detail, but reads more cleanly at ~22pt):

```sh
magick taicon.png -alpha extract \
  -background black -alpha shape \
  PNG32:taicon-template.png
```
