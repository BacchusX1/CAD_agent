import re
import cadquery as cq
from cadquery import exporters
import os

# ------------------------------------------------------------
# Simple DSL Parser
# ------------------------------------------------------------
def parse_dsl(dsl_text):
    commands = []
    for line in dsl_text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        cmd = parts[0]
        args = {}

        for p in parts[1:]:
            if "=" in p:
                k, v = p.split("=", 1)
                v = v.strip('"')

                # convert numbers robustly
                try:
                    # handle signs and decimals properly
                    if re.match(r"^-?\d+(\.\d+)?$", v):
                        v = float(v)
                except Exception:
                    pass

                args[k] = v

        commands.append({"cmd": cmd, "args": args})
    return commands


# ------------------------------------------------------------
# Translator (DSL -> CadQuery)
# ------------------------------------------------------------
def execute_dsl(commands, output_dir="out"):
    solids = {}

    for entry in commands:
        cmd = entry["cmd"].upper()
        args = entry["args"]

        if cmd == "CREATE_BOX":
            solids[args["id"]] = cq.Workplane("XY").box(
                args["width"], args["height"], args["depth"]
            )

        elif cmd == "CREATE_CYLINDER":
            solids[args["id"]] = cq.Workplane("XY").cylinder(
                args["height"], args["radius"]
            )

        elif cmd == "TRANSLATE":
            sid = args["id"]
            if sid in solids:
                solids[sid] = solids[sid].translate((args.get("x", 0), args.get("y", 0), args.get("z", 0)))

        elif cmd == "SUBTRACT":
            target = solids[args["target"]]
            tool = solids[args["tool"]]
            solids[args["target"]] = target.cut(tool)

        elif cmd == "FILLET":
            sid = args["id"]
            solids[sid] = solids[sid].edges().fillet(args["radius"])

        elif cmd == "EXPORT":
            os.makedirs(output_dir, exist_ok=True)
            filename = args["filename"]
            # use the last created or last target as main
            last_key = list(solids.keys())[-1]
            exporters.export(solids[last_key], os.path.join(output_dir, filename))

    print("✅ Export done in", output_dir)


# ------------------------------------------------------------
# Test run
# ------------------------------------------------------------
if __name__ == "__main__":
    dsl = """
    CREATE_BOX id=block width=60 height=30 depth=15
    CREATE_CYLINDER id=hole1 radius=5 height=20
    TRANSLATE id=hole1 x=-20 y=0 z=0
    CREATE_CYLINDER id=hole2 radius=5 height=20
    TRANSLATE id=hole2 x=20 y=0 z=0
    SUBTRACT target=block tool=hole1
    SUBTRACT target=block tool=hole2
    EXPORT filename="block_with_holes.step"
    """
    cmds = parse_dsl(dsl)
    execute_dsl(cmds)
