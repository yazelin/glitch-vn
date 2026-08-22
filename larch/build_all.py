#!/usr/bin/env python3
"""照順序跑完七章。單章除錯還是直接跑 build_chNN.py。"""
import pathlib, runpy, sys
here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here))
for p in sorted(here.glob("build_ch*.py")):
    print(f"\n── {p.stem} ──")
    runpy.run_path(str(p), run_name="__main__")
