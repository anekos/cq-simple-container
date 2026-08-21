# simple-container

A parametric open-top box with dividers.

```bash
uv run simple-container build                       # dist/v{N}-....stl
uv run simple-container build --width 200 --show
uv run simple-container build --depth-measure inner --depth 60
```

## Parameters

| Option | Default | Meaning |
| --- | --- | --- |
| `--width` | `120` | Size along X |
| `--height` | `120` | Size along Z |
| `--depth` | `80` | Size along Y |
| `--width-measure` / `--height-measure` / `--depth-measure` | `outer` | `outer` or `inner` — whether the value above is the outer size or the cavity size |
| `--thickness` | `2` | Wall / floor / divider thickness |
| `--fillet` | `3` | Radius of the vertical corners (`0` disables) |
| `--width-dividers` | `1` | Dividers perpendicular to X |
| `--depth-dividers` | `2` | Dividers perpendicular to Y |

The box is open at the top, so `--height-measure inner` only adds the floor
thickness, while the width and depth add two walls each.

Dividers split the cavity into equal cells: `n` dividers give `n + 1` cells, so
the default `1 x 2` yields a 2 x 3 grid. They run the full inner height, flush
with the top of the walls.
