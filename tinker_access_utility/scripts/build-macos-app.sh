#!/usr/bin/env bash
# Build TinkerAccessUtility.app + .dmg from pre-built universal binaries.
#
# Inputs (env vars):
#   APPLET_BIN  — path to the universal tinker_access_utility_applet binary
#   CLI_BIN     — path to the universal tinker_access_utility binary
#   ICON_PNG    — path to source icon PNG (≥ 1024×1024 recommended)
#   VERSION     — semver string written into Info.plist
#   OUT_DIR     — directory to emit .app and .dmg into (created if missing)
#
# Requires macOS host: uses `sips`, `iconutil`, and `hdiutil`.

set -euo pipefail

: "${APPLET_BIN:?APPLET_BIN is required}"
: "${CLI_BIN:?CLI_BIN is required}"
: "${ICON_PNG:?ICON_PNG is required}"
: "${VERSION:?VERSION is required}"
: "${OUT_DIR:?OUT_DIR is required}"

APP_NAME="TinkerAccessUtility"
BUNDLE_ID="org.tinkermill.tinker-access-utility"
DISPLAY_NAME="TinkerAccess Utility"
MIN_OS="10.13"

mkdir -p "$OUT_DIR"
APP_DIR="$OUT_DIR/$APP_NAME.app"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR/Contents/MacOS" "$APP_DIR/Contents/Resources"

cp "$APPLET_BIN" "$APP_DIR/Contents/MacOS/tinker_access_utility_applet"
cp "$CLI_BIN"    "$APP_DIR/Contents/MacOS/tinker_access_utility"
chmod +x "$APP_DIR/Contents/MacOS/"*

ICONSET="$OUT_DIR/$APP_NAME.iconset"
rm -rf "$ICONSET"
mkdir -p "$ICONSET"
sips -z   16   16 "$ICON_PNG" --out "$ICONSET/icon_16x16.png"      >/dev/null
sips -z   32   32 "$ICON_PNG" --out "$ICONSET/icon_16x16@2x.png"   >/dev/null
sips -z   32   32 "$ICON_PNG" --out "$ICONSET/icon_32x32.png"      >/dev/null
sips -z   64   64 "$ICON_PNG" --out "$ICONSET/icon_32x32@2x.png"   >/dev/null
sips -z  128  128 "$ICON_PNG" --out "$ICONSET/icon_128x128.png"    >/dev/null
sips -z  256  256 "$ICON_PNG" --out "$ICONSET/icon_128x128@2x.png" >/dev/null
sips -z  256  256 "$ICON_PNG" --out "$ICONSET/icon_256x256.png"    >/dev/null
sips -z  512  512 "$ICON_PNG" --out "$ICONSET/icon_256x256@2x.png" >/dev/null
sips -z  512  512 "$ICON_PNG" --out "$ICONSET/icon_512x512.png"    >/dev/null
sips -z 1024 1024 "$ICON_PNG" --out "$ICONSET/icon_512x512@2x.png" >/dev/null
iconutil -c icns "$ICONSET" -o "$APP_DIR/Contents/Resources/$APP_NAME.icns"
rm -rf "$ICONSET"

cat > "$APP_DIR/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$DISPLAY_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleExecutable</key>
    <string>tinker_access_utility_applet</string>
    <key>CFBundleIconFile</key>
    <string>$APP_NAME</string>
    <key>LSUIElement</key>
    <true/>
    <key>LSMinimumSystemVersion</key>
    <string>$MIN_OS</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

DMG_STAGING="$OUT_DIR/dmg-staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"
cp -R "$APP_DIR" "$DMG_STAGING/"
ln -s /Applications "$DMG_STAGING/Applications"

DMG_PATH="$OUT_DIR/$APP_NAME-$VERSION-universal.dmg"
rm -f "$DMG_PATH"
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$DMG_STAGING" \
    -ov -format UDZO \
    "$DMG_PATH"
rm -rf "$DMG_STAGING"

echo "Built: $APP_DIR"
echo "Built: $DMG_PATH"
