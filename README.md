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
| `--partition` | `2x3` | Partition expression dividing the cavity into cells (preview with `uv run app partition`) |

The box is open at the top, so `--height-measure inner` only adds the floor
thickness, while the width and depth add two walls each.

Dividers run the full inner height, flush with the top of the walls.
