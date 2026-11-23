from context import O

def main():
 assert (O/'NUMERIC_ADMISSION.json').is_file(),'ORIGINAL_RESPONSE_NUMERIC_ADMISSION_MISSING'
 from numeric_target import main as run
 return run()
if __name__=='__main__':raise SystemExit(main())
