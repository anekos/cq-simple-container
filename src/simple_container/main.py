from typing import Literal

import cadquery as cq
from click_cadquery import BuildParam
from click_cadquery.git import version_number as ver
from click_cadquery.partition import (
    Layout,
    PartitionError,
    PartitionExpr,
    Rect,
    parse,
    solve,
    walls_solid,
)
from pydantic import model_validator

Measure = Literal["outer", "inner"]
"""Whether a given dimension is the outer size or the inner (cavity) size."""


class Param(BuildParam):
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

    partition: PartitionExpr = PartitionExpr("2x3")
    """Divider layout: N | NxM | '30,40,*' | '1:2:1' | '30(3),*' (nesting flips axis)."""

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

    def layout(self) -> Layout:
        return solve(
            parse(self.partition),
            Rect(
                -self.inner_width / 2,
                -self.inner_depth / 2,
                self.inner_width,
                self.inner_depth,
            ),
            self.thickness,
        )

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
        try:
            self.layout()
        except PartitionError as e:
            raise ValueError(f"the partition does not fit: {e}") from e
        return self

    @property
    def filename(self) -> str:
        return (
            f"v{ver()}"
            f"-{self.outer_width:g}w{self.outer_height:g}h{self.outer_depth:g}d"
            f"-{self.thickness:g}t{self.fillet:g}r"
            f"-{self.partition.translate(_FILENAME_SAFE)}div"
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

    return result
