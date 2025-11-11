# test_cad.py
import cadquery as cq
from cadquery import exporters
import os

# create a simple box
result = cq.Workplane("XY").box(30, 20, 10)  # 30x20x10 mm box

outdir = "out"
os.makedirs(outdir, exist_ok=True)
step_path = os.path.join(outdir, "box.step")
stl_path  = os.path.join(outdir, "box.stl")

# export
exporters.export(result, step_path)
exporters.export(result, stl_path)

print("Exported:", step_path, stl_path)
