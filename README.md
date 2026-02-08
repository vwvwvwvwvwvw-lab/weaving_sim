# weaving_sim

### Run tests
```
pytest -q
```

### Linting
```
ruff check
ruff format
```

## Cool Weaves

### Plain Weave
```
    PCFG = PatternConfig(
        twill_over=1,
        twill_under=1,
        twill_step=1,
        broken_block=0,      # off
        broken_axes="cols",
    )

    DARK = "#1c7bda"   # blue
    LIGHT = "#f8fafc"  # near-white

    WARP_COLORS = thread_sequence(
                        [(DARK, 1)],
                        RCFG.cols
                        )
    WEFT_COLORS = thread_sequence(
                                [(LIGHT, 1)],
                                RCFG.cols
                                )
```
### 3 / 1 Twill
```
PCFG = PatternConfig(
    twill_over=3,
    twill_under=1,
    twill_step=1,

    broken_block=None,
    broken_axes="both",
)
```
### Houndstooth
```
    PCFG = PatternConfig(
        weave_over=2,
        weave_under=2,
        weave_step=1,

        broken_block=4,
        broken_axes="both",
    )
    DARK = "#1c7bda"   # blue
    LIGHT = "#f8fafc"  # near-white

    WARP_COLORS = thread_sequence(
                        [(DARK, 4), (LIGHT, 4)],
                        RCFG.cols
                        )
    WEFT_COLORS = thread_sequence(
                                [(LIGHT, 4), (DARK, 4),],
                                RCFG.cols
                                )
```

### Satin

```
Not yet implemented.
Can fake it with with very lopsided twills in the meantime.
```