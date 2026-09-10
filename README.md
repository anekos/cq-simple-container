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
| `--slit-side` | `none` | Side wall to cut a U-shaped slit into: `front`/`back` (-Y/+Y) or `left`/`right` (-X/+X) |
| `--slit-width` | `25` | Width of the slit = diameter of its semicircular bottom |
| `--slit-depth` | half the height | Distance from the top edge down to the lowest point of the slit |

The box is open at the top, so `--height-measure inner` only adds the floor
thickness, while the width and depth add two walls each.

Dividers run the full inner height, flush with the top of the walls.

The slit is cut through the chosen wall after the box is built, open at the
top edge, so contents can be pushed up and lifted out. It must fit the flat
part of the wall (between the corner fillets) and stop above the floor.
