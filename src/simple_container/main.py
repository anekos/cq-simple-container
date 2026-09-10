from typing import Literal

import cadquery as cq
from click_cadquery import BuildParam
from click_cadquery.git import version_number as ver
from click_cadquery.partition import (
    PartitionExpr,
    PartitionParam,
    partition_field,
    walls_solid,
)
from pydantic import model_validator

Measure = Literal["outer", "inner"]
"""Whether a given dimension is the outer size or the inner (cavity) size."""

SlitSide = Literal["none", "front", "back", "left", "right"]
"""Which side wall carries the U-shaped slit: front/back face -Y/+Y,
left/right face -X/+X."""


# PartitionParam supplies layout() and the partition-must-fit validation.
class Param(BuildParam, PartitionParam):
    width: float = 120.0
    """Size along X."""
    width_measure: Measure = "outer"

    height: float = 120.0
    """Size along Z. The box is open at the top, so only the floor is subtracted."""
    height_measure: Measure = "outer"

    depth: float = 80.0
    """Size along Y."""
    depth_measure: Measure = "outer"

    thickness: float = 2.0
    """Wall, floor and divider thickness."""

    fillet: float = 3.0
    """Radius of the vertical corners. 0 disables filleting."""

    partition: PartitionExpr = partition_field("2x3")

    slit_side: SlitSide = "none"
    """Cut a U-shaped slit into this side wall, open at the top, for
    lifting the contents out. "none" disables it."""

    slit_width: float = 25.0
    """Width of the slit = diameter of its semicircular bottom."""

    slit_depth: float | None = None
    """Distance from the top edge down to the lowest point of the slit.
    Defaults to half the outer height."""

    @property
    def outer_width(self) -> float:
        return self._outer(self.width, self.width_measure, 2)

    @property
    def outer_depth(self) -> float:
        return self._outer(self.depth, self.depth_measure, 2)

    @property
    def outer_height(self) -> float:
        # Open top: only the floor adds to the height.
        return self._outer(self.height, self.height_measure, 1)

    @property
    def inner_width(self) -> float:
        return self.outer_width - 2 * self.thickness

    @property
    def inner_depth(self) -> float:
        return self.outer_depth - 2 * self.thickness

    @property
    def inner_height(self) -> float:
        return self.outer_height - self.thickness

    def _outer(self, value: float, measure: Measure, walls: int) -> float:
        return value if measure == "outer" else value + walls * self.thickness

    @model_validator(mode="after")
    def _check(self) -> "Param":
        if self.thickness <= 0:
            raise ValueError("thickness must be positive")
        if self.fillet < 0:
            raise ValueError("fillet must not be negative")
        if min(self.inner_width, self.inner_depth, self.inner_height) <= 0:
            raise ValueError(
                "the walls do not fit: inner size is "
                f"{self.inner_width} x {self.inner_depth} x {self.inner_height}"
            )
        if self.fillet > min(self.outer_width, self.outer_depth) / 2:
            raise ValueError("fillet is too large for the outer size")
        if self.slit_side != "none":
            if self.slit_width <= 0:
                raise ValueError("slit_width must be positive")
            span = (
                self.outer_width
                if self.slit_side in ("front", "back")
                else self.outer_depth
            )
            flat = span - 2 * max(self.fillet, self.thickness)
            if self.slit_width > flat:
                raise ValueError(
                    "slit_width does not fit the flat part of the "
                    f"{self.slit_side} wall (at most {flat:g})"
                )
            if self.slit_depth is None:
                self.slit_depth = self.outer_height / 2
            if self.slit_depth < self.slit_width / 2:
                raise ValueError(
                    "slit_depth must be at least slit_width / 2 "
                    "(the semicircular bottom)"
                )
            if self.slit_depth > self.inner_height:
                raise ValueError(
                    "the slit would cut into the floor: "
                    f"slit_depth must be at most {self.inner_height:g}"
                )
        return self

    @property
    def filename(self) -> str:
        slit = (
            f"-{self.slit_side}{self.slit_width:g}x{self.slit_depth:g}slit"
            if self.slit_side != "none"
            else ""
        )
        return (
            f"v{ver()}"
            f"-{self.outer_width:g}w{self.outer_height:g}h{self.outer_depth:g}d"
            f"-{self.thickness:g}t{self.fillet:g}r"
            f"-{self.partition.translate(_FILENAME_SAFE)}div"
            f"{slit}"
            ".stl"
        )


# Shell- and glob-unsafe characters of partition expressions, mapped for filenames.
_FILENAME_SAFE = str.maketrans({"*": "@", ",": "+", "(": "[", ")": "]", ":": "="})


def build(param: Param) -> cq.Workplane:
    t = param.thickness

    result = cq.Workplane("XY").box(
        param.outer_width,
        param.outer_depth,
        param.outer_height,
        centered=(True, True, False),
    )

    if param.fillet > 0:
        result = result.edges("|Z").fillet(param.fillet)

    result = result.faces(">Z").shell(-t)

    # Dividers overlap the surrounding walls by t/2 on each end so that the union
    # never has to merge coincident faces.
    walls = walls_solid(param.layout(), param.inner_height)
    if walls is not None:
        result = result.union(walls.translate((0, 0, t)))

    if param.slit_side != "none":
        result = result.cut(_slit_cutter(param))

    return result


def _slit_cutter(param: Param) -> cq.Workplane:
    """A solid covering the U-shaped slit: a rectangle running past the top
    edge, closed at the bottom by a semicircle of diameter slit_width. It
    spans the wall thickness with margin on both sides (0.1 into the cavity,
    1.0 outward) so the cut never leaves coincident faces."""
    assert param.slit_depth is not None
    r = param.slit_width / 2
    # Center of the semicircle; the lowest point of the slit sits slit_depth
    # below the top edge.
    z_center = param.outer_height - param.slit_depth + r
    z_top = param.outer_height + 1.0
    thick = param.thickness + 1.1

    # Sketch plane sits just inside the inner wall face; extrusion runs
    # outward through the wall (negative amounts go against the plane normal).
    plane, origin, amount = {
        "front": ("XZ", (0, -param.outer_depth / 2 + param.thickness + 0.1, 0), thick),
        "back": ("XZ", (0, param.outer_depth / 2 - param.thickness - 0.1, 0), -thick),
        "left": ("YZ", (-param.outer_width / 2 + param.thickness + 0.1, 0, 0), -thick),
        "right": ("YZ", (param.outer_width / 2 - param.thickness - 0.1, 0, 0), thick),
    }[param.slit_side]

    return (
        cq.Workplane(plane, origin=cq.Vector(origin))
        .moveTo(-r, z_top)
        .lineTo(-r, z_center)
        .threePointArc((0, z_center - r), (r, z_center))
        .lineTo(r, z_top)
        .close()
        .extrude(amount)
    )
