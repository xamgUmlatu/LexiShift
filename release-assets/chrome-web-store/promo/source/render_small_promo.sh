#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd -- "$script_dir/../../../.." && pwd)
icon_path="$repo_root/apps/chrome-extension/icons/icon128.png"
output_dir="$script_dir/../final"
output_path="$output_dir/small-promo-440x280.png"
render_tmp=$(mktemp -d)
trap 'rm -rf "$render_tmp"' EXIT

mkdir -p "$output_dir"

magick -size 440x280 gradient:'#0d3038-#176e74' \
  \( -size 440x280 xc:none \
     -fill 'rgba(65,203,208,0.25)' -draw 'circle 48,18 185,18' \
     -fill 'rgba(255,174,50,0.19)' -draw 'circle 430,285 300,285' \
     -blur 0x34 \) \
  -compose over -composite \
  "$render_tmp/background.png"

magick -size 440x280 xc:none \
  -fill 'rgba(201,244,239,0.26)' \
  -draw 'roundrectangle 214,65 358,73 4,4' \
  -draw 'roundrectangle 370,65 408,73 4,4' \
  -draw 'roundrectangle 214,88 286,96 4,4' \
  -draw 'roundrectangle 298,88 408,96 4,4' \
  -draw 'roundrectangle 214,111 332,119 4,4' \
  -draw 'roundrectangle 344,111 408,119 4,4' \
  -fill '#ffaf31' -draw 'roundrectangle 292,84 348,100 8,8' \
  -fill '#65d9d3' -draw 'roundrectangle 333,107 382,123 8,8' \
  "$render_tmp/reading-lines.png"

magick "$icon_path" -channel A -shadow 45x10+0+9 \
  "$render_tmp/icon-shadow.png"

magick "$render_tmp/background.png" \
  "$render_tmp/reading-lines.png" -compose over -composite \
  "$render_tmp/icon-shadow.png" -geometry +39+47 -compose over -composite \
  "$icon_path" -geometry +48+56 -compose over -composite \
  -font Avenir-Next-Bold -pointsize 38 -fill '#f8fffc' \
  -annotate +220+171 'LexiShift' \
  -fill '#9ce5df' -draw 'roundrectangle 221,183 375,186 1.5,1.5' \
  -fill '#ffad2e' -draw 'circle 405,32 410,32' \
  -stroke 'rgba(136,227,220,0.42)' -strokewidth 2 -fill none \
  -draw "path 'M 397,238 C 355,219 322,224 284,247'" \
  -stroke none -fill '#ffad2e' -draw 'circle 279,250 283,250' \
  -alpha remove -alpha off -type TrueColor \
  "PNG24:$output_path"

magick identify -format '%f %wx%h %[channels] %[type]\n' "$output_path"
