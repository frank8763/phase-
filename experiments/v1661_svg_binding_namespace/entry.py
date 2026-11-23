"""The numerical worker cannot bind author code without exact new admission."""
from context import O,read

def main():
 assert (O/'NUMERIC_ADMISSION.json').is_file(),'SVG_NUMERIC_ADMISSION_MISSING'
 from numeric_target import main as run
 return run()
if __name__=='__main__':raise SystemExit(main())
