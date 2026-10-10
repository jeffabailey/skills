#!/usr/bin/env bash
# Render a page at desktop (1280px) and a TRUE phone viewport (390px), light and
# dark, and measure horizontal overflow at 390px.
#
# Usage: render.sh <page.html | http(s)://url> <outdir> [prefix]
#   prefix defaults to "after"; run once with "before" on the original first.
# Env:   CHROME=/path/to/chrome (auto-detected otherwise)
#
# Why the iframe: `chrome --headless --window-size=390,...` lays the page out
# wider than 390px and clips the screenshot, which looks like a pass when it is
# not. An iframe that is exactly 390px wide gives the page a real 390px viewport.
set -euo pipefail

target="${1:?usage: render.sh <page.html|url> <outdir> [prefix]}"
outdir="${2:?usage: render.sh <page.html|url> <outdir> [prefix]}"
prefix="${3:-after}"
mkdir -p "$outdir"
outdir="$(cd "$outdir" && pwd)"

if [[ -z "${CHROME:-}" ]]; then
  for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
           "/Applications/Chromium.app/Contents/MacOS/Chromium" \
           google-chrome google-chrome-stable chromium chromium-browser; do
    if [[ -x "$c" ]] || command -v "$c" >/dev/null 2>&1; then CHROME="$c"; break; fi
  done
fi
[[ -n "${CHROME:-}" ]] || { echo "NOT VERIFIED: no Chrome/Chromium found (set CHROME=...)"; exit 2; }

case "$target" in
  http://*|https://*|file://*) url="$target" ;;
  *) url="file://$(cd "$(dirname "$target")" && pwd)/$(basename "$target")" ;;
esac

chrome() { "$CHROME" --headless=new --disable-gpu --hide-scrollbars --no-first-run \
  --allow-file-access-from-files --virtual-time-budget=3000 "$@" 2>/dev/null; }

harness="$outdir/$prefix-390-harness.html"
cat > "$harness" <<HTML
<!doctype html><meta charset="utf-8"><body style="margin:0">
<iframe id="f" src="$url" style="width:390px;height:844px;border:0"></iframe>
<pre id="out">overflow: unknown</pre>
<script>
document.getElementById('f').addEventListener('load', function () {
  var o = document.getElementById('out');
  try {
    var d = this.contentDocument.documentElement;
    var w = Math.max(d.scrollWidth, this.contentDocument.body ? this.contentDocument.body.scrollWidth : 0);
    o.textContent = (w > 390 ? 'overflow: FAIL ' : 'overflow: ok ') + 'scrollWidth=' + w + ' viewport=390';
  } catch (e) { o.textContent = 'overflow: unknown (cross-origin; inspect the screenshot)'; }
});
</script>
HTML

for scheme in light dark; do
  flag=(); [[ $scheme == dark ]] && flag=(--force-dark-mode --blink-settings=preferredColorScheme=0)
  chrome "${flag[@]}" --window-size=1280,900 --screenshot="$outdir/$prefix-1280-$scheme.png" "$url" >/dev/null || true
  chrome "${flag[@]}" --window-size=390,900  --screenshot="$outdir/$prefix-390-$scheme.png" "file://$harness" >/dev/null || true
done

result="$(chrome --window-size=600,1000 --dump-dom "file://$harness" | sed -n 's/.*<pre id="out">\([^<]*\)<\/pre>.*/\1/p')"
echo "screenshots: $outdir/$prefix-{1280,390}-{light,dark}.png"
echo "390px ${result:-overflow: unknown (dump-dom returned nothing)}"
echo "Compare light vs dark shots: identical images mean the page has no dark scheme."
