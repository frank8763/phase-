"""Bound one registered child main to its previously reserved writer cap."""
import importlib.util
from pathlib import Path
C=Path(__file__).resolve().parent

def exact(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def run(main):
 budget=exact('v1432_child_writer_budget',C/'writer_budget.py').WriterBudget.from_environment()
 boundary=exact('v1432_child_actual_output_boundary',C/'bounded_io.py').OutputBoundary
 with boundary(budget.output,budget.reserve):return main()
