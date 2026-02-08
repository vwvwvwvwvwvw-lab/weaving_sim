"""
Turtle Weaving Simulator: plain, twill, satin
NOW: renders real over/under at each crossing using the pattern matrix.

At each crossing:
- The thread on top gets a lighter highlight segment of its own color.
- The thread underneath gets a darker shadow segment of its own color.
"""

import turtle as t
from dataclasses import dataclass
from typing import List, Optional, Tuple, Iterable


# ----------------------------
# Helpers: colors (repeat + shade)
# ----------------------------


def thread_sequence(
    runs: Iterable[Tuple[str, int]],
    count: int,
) -> List[str]:
    """
    Expand color runs into a repeating list.

    Example:
      thread_sequence([("#000", 1), ("#fff", 1)], 6)
        -> #000 #fff #000 #fff #000 #fff

      thread_sequence([("#000", 4), ("#fff", 4)], 16)
        -> #### #### #### ####
    """
    if count <= 0:
        return []

    seq: List[str] = []
    for color, n in runs:
        if n <= 0:
            raise ValueError("run lengths must be > 0")
        seq.extend([color] * n)

    if not seq:
        raise ValueError("runs must not be empty")

    out: List[str] = []
    while len(out) < count:
        out.extend(seq)

    return out[:count]


def repeat_colors(colors: List[str], count: int) -> List[str]:
    return thread_sequence([(c, 1) for c in colors], count)


def block_repeat(color_a: str, color_b: str, block: int, count: int) -> List[str]:
    return thread_sequence([(color_a, block), (color_b, block)], count)


def _hex_to_rgb(h: str) -> Tuple[int, int, int]:
    s = h.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        raise ValueError(f"Expected hex color like #RRGGBB, got: {h}")
    return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)


def _rgb_to_hex(r: float, g: float, b: float) -> str:
    r = max(0, min(255, int(round(r))))
    g = max(0, min(255, int(round(g))))
    b = max(0, min(255, int(round(b))))
    return f"#{r:02x}{g:02x}{b:02x}"


def shade(color_hex: str, factor: float) -> str:
    """
    factor > 1.0 => lighten toward white
    factor < 1.0 => darken toward black
    """
    r, g, b = _hex_to_rgb(color_hex)
    if factor >= 1.0:
        k = factor - 1.0
        r2 = r + (255 - r) * k
        g2 = g + (255 - g) * k
        b2 = b + (255 - b) * k
    else:
        r2 = r * factor
        g2 = g * factor
        b2 = b * factor
    return _rgb_to_hex(r2, g2, b2)


# ----------------------------
# Pattern generation
# ----------------------------


@dataclass
class PatternConfig:
    # Twill settings
    weave_over: int = 3
    weave_under: int = 1
    weave_step: int = 1

    # Broken twill (optional)
    broken_block: Optional[int] = None
    broken_axes: str = "both"  # "rows", "cols", "both"


def make_pattern(rows: int, cols: int, pcfg: PatternConfig) -> List[List[bool]]:
    over = max(1, int(pcfg.weave_over))
    under = max(1, int(pcfg.weave_under))
    period = over + under
    step = int(pcfg.weave_step)
    if step == 0:
        step = 1  # twill needs a step to form a diagonal

    broken = pcfg.broken_block
    if broken is not None and int(broken) <= 0:
        broken = None  # treat 0 as "off"
    axes = pcfg.broken_axes.lower().strip()

    patt: List[List[bool]] = []
    for r in range(rows):
        dir_r = 1
        if broken and axes in ("rows", "both"):
            dir_r = 1 if ((r // broken) % 2 == 0) else -1

        row: List[bool] = []
        for c in range(cols):
            dir_c = 1
            if broken and axes in ("cols", "both"):
                dir_c = 1 if ((c // broken) % 2 == 0) else -1

            direction = dir_r * dir_c
            phase = (c - direction * r * step) % period
            row.append(phase < over)  # True = warp over
        patt.append(row)
    return patt


# ----------------------------
# Rendering
# ----------------------------


@dataclass
class RenderConfig:
    rows: int = 24
    cols: int = 24
    cell: int = 18
    thread: int = 9
    margin: int = 40
    speed: int = 0
    show_grid: bool = False


@dataclass
class ColorConfig:
    warp_thread_colors: List[str]  # length cols
    weft_thread_colors: List[str]  # length rows
    background: str = "#f7fafc"
    grid: str = "#e2e8f0"
    highlight_factor: float = 1.18  # top thread highlight
    shadow_factor: float = 0.72  # bottom thread shadow


def _setup_screen(cfg: RenderConfig, bg: str) -> t.Screen:
    scr = t.Screen()
    width = cfg.margin * 2 + cfg.cols * cfg.cell
    height = cfg.margin * 2 + cfg.rows * cfg.cell
    scr.setup(width=width + 40, height=height + 40)
    scr.bgcolor(bg)
    scr.title("")
    return scr


def render_weave(
    pattern: List[List[bool]], rcfg: RenderConfig, ccfg: ColorConfig
) -> None:
    if len(pattern) != rcfg.rows or (pattern and len(pattern[0]) != rcfg.cols):
        raise ValueError("Pattern dimensions must match RenderConfig rows/cols")

    if len(ccfg.warp_thread_colors) != rcfg.cols:
        raise ValueError("warp_thread_colors length must equal cols")
    if len(ccfg.weft_thread_colors) != rcfg.rows:
        raise ValueError("weft_thread_colors length must equal rows")

    scr = _setup_screen(rcfg, ccfg.background)
    scr.tracer(False)

    pen = t.Turtle(visible=False)
    pen.speed(rcfg.speed)
    pen.hideturtle()

    origin_x = -(rcfg.cols * rcfg.cell) / 2
    origin_y = -(rcfg.rows * rcfg.cell) / 2

    def goto(x: float, y: float) -> None:
        pen.penup()
        pen.goto(x, y)
        pen.pendown()

    def seg(
        p1: Tuple[float, float], p2: Tuple[float, float], color: str, width: int
    ) -> None:
        pen.pencolor(color)
        pen.width(width)
        goto(p1[0], p1[1])
        pen.goto(p2[0], p2[1])

    if rcfg.show_grid:
        g = t.Turtle(visible=False)
        g.speed(0)
        g.pencolor(ccfg.grid)
        g.width(1)
        for c in range(rcfg.cols + 1):
            x = origin_x + c * rcfg.cell
            g.penup()
            g.goto(x, origin_y)
            g.pendown()
            g.goto(x, origin_y + rcfg.rows * rcfg.cell)
        for r in range(rcfg.rows + 1):
            y = origin_y + r * rcfg.cell
            g.penup()
            g.goto(origin_x, y)
            g.pendown()
            g.goto(origin_x + rcfg.cols * rcfg.cell, y)

    # Draw per-cell crossings so over/under is visible
    gap = rcfg.thread * 0.55  # small "break" in the under-thread at the center

    for r in range(rcfg.rows):
        y = origin_y + (r + 0.5) * rcfg.cell
        weft_col = ccfg.weft_thread_colors[r]

        for c in range(rcfg.cols):
            x = origin_x + (c + 0.5) * rcfg.cell
            warp_col = ccfg.warp_thread_colors[c]
            warp_over = pattern[r][c]

            # segment endpoints inside the cell
            xL, xR = x - rcfg.cell / 2, x + rcfg.cell / 2
            yB, yT = y - rcfg.cell / 2, y + rcfg.cell / 2

            # Under-thread gets split with a gap at center
            if warp_over:
                # weft under
                under = shade(weft_col, ccfg.shadow_factor)
                seg((xL, y), (x - gap, y), under, rcfg.thread)
                seg((x + gap, y), (xR, y), under, rcfg.thread)
                # warp over (continuous)
                over = shade(warp_col, ccfg.highlight_factor)
                seg((x, yB), (x, yT), over, rcfg.thread)
            else:
                # warp under
                under = shade(warp_col, ccfg.shadow_factor)
                seg((x, yB), (x, y - gap), under, rcfg.thread)
                seg((x, y + gap), (x, yT), under, rcfg.thread)
                # weft over (continuous)
                over = shade(weft_col, ccfg.highlight_factor)
                seg((xL, y), (xR, y), over, rcfg.thread)

    scr.tracer(True)
    scr.update()
    scr.mainloop()


# ----------------------------
# Main: configure here
# ----------------------------

if __name__ == "__main__":
    RCFG = RenderConfig(rows=44, cols=44, cell=14, thread=10, speed=0, show_grid=False)

    PCFG = PatternConfig(
        weave_over=1,
        weave_under=8,
        weave_step=1,
        broken_block=4,
        broken_axes="both",
    )
    DARK = "#1c7bda"  # blue
    LIGHT = "#f8fafc"  # near-white

    WARP_COLORS = thread_sequence([(DARK, 1)], RCFG.cols)
    WEFT_COLORS = thread_sequence([(LIGHT, 1)], RCFG.cols)

    CCFG = ColorConfig(
        warp_thread_colors=WARP_COLORS,
        weft_thread_colors=WEFT_COLORS,
        shadow_factor=0.75,
    )

    pattern = make_pattern(RCFG.rows, RCFG.cols, PCFG)
    render_weave(pattern, RCFG, CCFG)
