"""Unqualified numerical/physical execution is explicitly refused."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]
O=R/'runs/v1656_svg_solver_interface'
def main():
 path=O/'NUMERIC_ADMISSION.json'
 assert path.is_file(),'SVG_NUMERIC_ADMISSION_MISSING'
 value=json.loads(path.read_text())
 assert value.get('models_authorized')is True,'SVG_NUMERIC_AUTHORITY_MISSING'
 raise AssertionError('SVG_NUMERIC_OWNER_NOT_YET_QUALIFIED')
if __name__=='__main__':main()
