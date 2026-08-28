from click_cadquery import define_app

from .main import Param, build

# The `partition` preview subcommand is registered automatically, since
# Param carries a PartitionExpr field and a layout() method.
main = define_app(Param, build)
