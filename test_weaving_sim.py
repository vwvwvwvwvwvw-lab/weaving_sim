import pytest


import weaving_sim as m


def test_thread_sequence_repeats_runs():
    out = m.thread_sequence([("#000000", 1), ("#ffffff", 1)], 6)
    assert out == ["#000000", "#ffffff", "#000000", "#ffffff", "#000000", "#ffffff"]


def test_thread_sequence_blocks():
    out = m.thread_sequence([("#000000", 2), ("#ffffff", 2)], 10)
    assert out == ["#000000", "#000000", "#ffffff", "#ffffff",
                   "#000000", "#000000", "#ffffff", "#ffffff",
                   "#000000", "#000000"]


def test_thread_sequence_count_zero_or_negative():
    assert m.thread_sequence([("#000", 1)], 0) == []
    assert m.thread_sequence([("#000", 1)], -5) == []


def test_thread_sequence_rejects_empty_runs():
    with pytest.raises(ValueError, match="runs must not be empty"):
        m.thread_sequence([], 5)


def test_thread_sequence_rejects_nonpositive_run_length():
    with pytest.raises(ValueError, match="run lengths must be > 0"):
        m.thread_sequence([("#000", 0)], 5)
    with pytest.raises(ValueError, match="run lengths must be > 0"):
        m.thread_sequence([("#000", -2)], 5)


def test_repeat_colors_is_thin_wrapper():
    out = m.repeat_colors(["a", "b", "c"], 8)
    assert out == ["a", "b", "c", "a", "b", "c", "a", "b"]


def test_block_repeat():
    out = m.block_repeat("X", "Y", block=3, count=10)
    assert out == ["X", "X", "X", "Y", "Y", "Y", "X", "X", "X", "Y"]


@pytest.mark.parametrize(
    "hex_in, rgb",
    [
        ("#000000", (0, 0, 0)),
        ("#ffffff", (255, 255, 255)),
        ("#0a0b0c", (10, 11, 12)),
        ("0a0b0c",  (10, 11, 12)),  # leading # optional
    ],
)
def test_hex_to_rgb(hex_in, rgb):
    assert m._hex_to_rgb(hex_in) == rgb


@pytest.mark.parametrize("bad", ["", "#fff", "#12345", "1234567", "#zzzzzz"])
def test_hex_to_rgb_rejects_bad(bad):
    # "#zzzzzz" will fail in int(..., 16) with ValueError too
    with pytest.raises(ValueError):
        m._hex_to_rgb(bad)


def test_rgb_to_hex_rounds_and_clamps():
    assert m._rgb_to_hex(0, 0, 0) == "#000000"
    assert m._rgb_to_hex(255, 255, 255) == "#ffffff"
    assert m._rgb_to_hex(12.4, 12.5, 12.6) == "#0c0c0d"  # round()
    assert m._rgb_to_hex(-5, 999, 1) == "#00ff01"        # clamp


def test_shade_lighten_and_darken_known_values():
    # darken pure white by half
    assert m.shade("#ffffff", 0.5) == "#808080"
    # lighten pure black by 50% toward white: 0 + (255-0)*0.5 = 127.5 -> 128
    assert m.shade("#000000", 1.5) == "#808080"
    # factor == 1.0 is identity
    assert m.shade("#1c7bda", 1.0) == "#1c7bda"


def test_make_pattern_dimensions():
    pcfg = m.PatternConfig(weave_over=2, weave_under=1, weave_step=1)
    patt = m.make_pattern(3, 5, pcfg)
    assert len(patt) == 3
    assert all(len(row) == 5 for row in patt)
    assert all(isinstance(v, bool) for row in patt for v in row)


def test_make_pattern_step_zero_treated_as_one():
    pcfg0 = m.PatternConfig(weave_over=2, weave_under=1, weave_step=0)
    pcfg1 = m.PatternConfig(weave_over=2, weave_under=1, weave_step=1)
    assert m.make_pattern(6, 6, pcfg0) == m.make_pattern(6, 6, pcfg1)

def test_make_pattern_changes_with_broken_twill():
    base = m.PatternConfig(weave_over=3, weave_under=1, weave_step=1, broken_block=None)
    broken = m.PatternConfig(weave_over=3, weave_under=1, weave_step=1, broken_block=2, broken_axes="both")
    p0 = m.make_pattern(8, 8, base)
    p1 = m.make_pattern(8, 8, broken)
    assert p0 != p1  # should differ when broken twill is on


def test_make_pattern_broken_block_zero_or_negative_is_off():
    pcfg_off = m.PatternConfig(weave_over=3, weave_under=1, weave_step=1, broken_block=None)
    pcfg_zero = m.PatternConfig(weave_over=3, weave_under=1, weave_step=1, broken_block=0, broken_axes="both")
    pcfg_neg = m.PatternConfig(weave_over=3, weave_under=1, weave_step=1, broken_block=-4, broken_axes="both")
    assert m.make_pattern(6, 6, pcfg_zero) == m.make_pattern(6, 6, pcfg_off)
    assert m.make_pattern(6, 6, pcfg_neg) == m.make_pattern(6, 6, pcfg_off)

class _FakeScreen:
    def tracer(self, *args, **kwargs): pass
    def update(self): pass
    def mainloop(self): pass

class _FakeTurtle:
    def __init__(self, visible=False): pass
    def speed(self, *args, **kwargs): pass
    def hideturtle(self): pass
    def penup(self): pass
    def pendown(self): pass
    def goto(self, *args, **kwargs): pass
    def pencolor(self, *args, **kwargs): pass
    def width(self, *args, **kwargs): pass


def _valid_configs(rows=2, cols=3):
    rcfg = m.RenderConfig(rows=rows, cols=cols, cell=10, thread=4, margin=1, speed=0, show_grid=False)
    ccfg = m.ColorConfig(
        warp_thread_colors=["#000000"] * cols,
        weft_thread_colors=["#ffffff"] * rows,
        background="#ffffff",
        grid="#cccccc",
        highlight_factor=1.1,
        shadow_factor=0.9,
    )
    return rcfg, ccfg


def test_render_weave_rejects_pattern_dim_mismatch(monkeypatch):
    # Patch screen + turtle so it won't open anything, even if it got that far
    monkeypatch.setattr(m, "_setup_screen", lambda cfg, bg: _FakeScreen())
    monkeypatch.setattr(m.t, "Turtle", _FakeTurtle)

    rcfg, ccfg = _valid_configs(rows=2, cols=3)
    bad_pattern = [[True, False]]  # 1x2, but rcfg says 2x3
    with pytest.raises(ValueError, match="Pattern dimensions must match"):
        m.render_weave(bad_pattern, rcfg, ccfg)


def test_render_weave_rejects_warp_color_length(monkeypatch):
    monkeypatch.setattr(m, "_setup_screen", lambda cfg, bg: _FakeScreen())
    monkeypatch.setattr(m.t, "Turtle", _FakeTurtle)

    rcfg, ccfg = _valid_configs(rows=2, cols=3)
    ccfg.warp_thread_colors = ["#000000"] * 2  # should be 3
    pattern = m.make_pattern(rcfg.rows, rcfg.cols, m.PatternConfig())
    with pytest.raises(ValueError, match="warp_thread_colors length must equal cols"):
        m.render_weave(pattern, rcfg, ccfg)


def test_render_weave_rejects_weft_color_length(monkeypatch):
    monkeypatch.setattr(m, "_setup_screen", lambda cfg, bg: _FakeScreen())
    monkeypatch.setattr(m.t, "Turtle", _FakeTurtle)

    rcfg, ccfg = _valid_configs(rows=2, cols=3)
    ccfg.weft_thread_colors = ["#ffffff"] * 1  # should be 2
    pattern = m.make_pattern(rcfg.rows, rcfg.cols, m.PatternConfig())
    with pytest.raises(ValueError, match="weft_thread_colors length must equal rows"):
        m.render_weave(pattern, rcfg, ccfg)
