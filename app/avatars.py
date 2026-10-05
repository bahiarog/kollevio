"""Deterministic abstract SVG avatar generation.

Each hired agent instance gets a visually distinct, premium-looking abstract
avatar derived from its `avatar_seed` (a random string assigned at hire time)
and the role's `color_accent` (a hex color). No external image APIs, no
photorealistic faces — pure generated vector geometry with soft gradients.
"""
import hashlib
import math
import colorsys


def _seed_bytes(seed: str) -> bytes:
    return hashlib.sha256(seed.encode("utf-8")).digest()


def _hex_to_hsl(hex_color: str):
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16) / 255
    g = int(hex_color[2:4], 16) / 255
    b = int(hex_color[4:6], 16) / 255
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h, s, l


def _hsl_to_hex(h, s, l) -> str:
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return "#{:02x}{:02x}{:02x}".format(int(r * 255), int(g * 255), int(b * 255))


def generate_avatar_svg(seed: str, color_accent: str = "#D97A3F", size: int = 120) -> str:
    """Return a self-contained <svg> string, deterministic for a given seed."""
    b = _seed_bytes(seed)
    h, s, l = _hex_to_hsl(color_accent)

    # Derive a small per-instance hue/lightness shift so each avatar of the
    # same role is distinct, while staying in the same family of color.
    hue_shift = ((b[0] / 255) - 0.5) * 0.12
    base_hue = (h + hue_shift) % 1.0
    accent_hex = _hsl_to_hex(base_hue, min(s + 0.05, 1.0), l)
    accent_light = _hsl_to_hex(base_hue, max(s - 0.15, 0), min(l + 0.28, 0.92))
    bg_dark = "#e9e7e2"

    cx, cy = size / 2, size / 2
    uid = hashlib.md5(seed.encode()).hexdigest()[:8]

    shapes = []
    shape_count = 3 + (b[1] % 3)  # 3-5 shapes
    for i in range(shape_count):
        bi = b[(i * 3) % len(b):]
        angle = (bi[0] / 255) * 360
        radius = size * (0.12 + (bi[1] / 255) * 0.28)
        dist = size * (0.05 + (bi[2 % len(bi)] / 255) * 0.22) if len(bi) > 2 else size * 0.1
        rad = math.radians(angle)
        ox = cx + dist * math.cos(rad)
        oy = cy + dist * math.sin(rad)
        opacity = 0.35 + (bi[0] / 255) * 0.5
        if i % 2 == 0:
            shapes.append(
                f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="{radius:.1f}" '
                f'fill="url(#g{uid})" opacity="{opacity:.2f}" />'
            )
        else:
            rot = angle
            shapes.append(
                f'<rect x="{ox - radius/2:.1f}" y="{oy - radius/2:.1f}" width="{radius:.1f}" '
                f'height="{radius:.1f}" rx="{radius*0.22:.1f}" fill="url(#g{uid})" '
                f'opacity="{opacity:.2f}" transform="rotate({rot:.0f} {ox:.1f} {oy:.1f})" />'
            )

    # Central core shape - always present, strongest accent
    core_r = size * 0.16
    shapes.append(
        f'<circle cx="{cx}" cy="{cy}" r="{core_r:.1f}" fill="{accent_hex}" opacity="0.9" />'
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}" role="img" aria-label="Agenten-Avatar">
  <defs>
    <radialGradient id="g{uid}" cx="35%" cy="30%" r="80%">
      <stop offset="0%" stop-color="{accent_light}" />
      <stop offset="100%" stop-color="{accent_hex}" />
    </radialGradient>
    <radialGradient id="bg{uid}" cx="50%" cy="40%" r="75%">
      <stop offset="0%" stop-color="#f8f7f4" />
      <stop offset="100%" stop-color="{bg_dark}" />
    </radialGradient>
  </defs>
  <circle cx="{cx}" cy="{cy}" r="{size/2}" fill="url(#bg{uid})" />
  {''.join(shapes)}
</svg>'''
    return svg
