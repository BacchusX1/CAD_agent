from llama_cpp import Llama
import re
import cadquery as cq
from cadquery import exporters
import os

MODEL_PATH = "/home/bacchus/.cache/huggingface/hub/models--TheBloke--Mistral-7B-Instruct-v0.2-GGUF/snapshots/3a6fbf4a41a1d52e415a4958cde6856d34b2db93/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
llm = Llama(model_path=MODEL_PATH, n_ctx=2048, n_threads=8)

# --------------------------
# DSL Parser
# --------------------------
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
                if re.match(r"^-?\d+(\.\d+)?$", v):
                    v = float(v)
                args[k] = v
        commands.append({"cmd": cmd, "args": args})
    return commands

# --------------------------
# DSL Validator
# --------------------------
def validate_dsl(commands):
    ids = set()
    available_ids = set()
    for entry in commands:
        cmd = entry["cmd"].upper()
        args = entry["args"]

        # Validate IDs
        if cmd.startswith("CREATE_") or cmd in ["TRANSLATE", "FILLET"]:
            sid = args.get("id")
            if not sid:
                return False, f"Missing 'id' in {cmd}"
            if cmd.startswith("CREATE_"):
                if sid in ids:
                    return False, f"Duplicate id '{sid}'"
                ids.add(sid)
                available_ids.add(sid)
            else:
                if sid not in available_ids:
                    return False, f"Unknown id '{sid}' in {cmd}"

        # Validate references
        if cmd == "SUBTRACT":
            if args.get("target") not in available_ids:
                return False, f"Unknown target '{args.get('target')}'"
            if args.get("tool") not in available_ids:
                return False, f"Unknown tool '{args.get('tool')}'"

        # Validate positive numbers
        for key, val in args.items():
            if isinstance(val, float) and val <= 0:
                if key in ["width", "height", "depth", "radius"]:
                    return False, f"{key} must be positive in {cmd}"

    return True, "Valid DSL"

# --------------------------
# DSL -> CadQuery executor
# --------------------------
def execute_dsl(commands, output_dir="out"):
    solids = {}
    main_part = None
    for entry in commands:
        cmd = entry["cmd"].upper()
        args = entry["args"]

        if cmd == "CREATE_BOX":
            solids[args["id"]] = cq.Workplane("XY").box(
                args["width"], args["height"], args["depth"]
            )
            if main_part is None:
                main_part = args["id"]

        elif cmd == "CREATE_CYLINDER":
            solids[args["id"]] = cq.Workplane("XY").cylinder(
                args["height"], args["radius"]
            )
            if main_part is None:
                main_part = args["id"]

        elif cmd == "TRANSLATE":
            sid = args["id"]
            x, y, z = float(args.get("x", 0)), float(args.get("y", 0)), float(args.get("z", 0))
            solids[sid] = solids[sid].translate((x, y, z))

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
            export_part = main_part if main_part else list(solids.keys())[-1]
            exporters.export(solids[export_part], os.path.join(output_dir, filename))
            return os.path.join(output_dir, filename)

    return None

# --------------------------
# NL -> DSL via LLM
# --------------------------
def nl_to_dsl(user_prompt):
    system_prompt = """
    You are a CAD design assistant.
    You receive a natural language request describing a simple 3D part.
    You must output ONLY valid DSL commands, EXACTLY following this grammar:

    Commands:
    CREATE_BOX id=<id> width=<float> height=<float> depth=<float>
    CREATE_CYLINDER id=<id> radius=<float> height=<float>
    TRANSLATE id=<id> x=<float> y=<float> z=<float>
    SUBTRACT target=<id> tool=<id>
    FILLET id=<id> radius=<float>
    EXPORT filename="<filename>"

    Rules:
    - Each command must be on its own line.
    - Start each new solid with a CREATE_* command.
    - All IDs must be unique strings (e.g., box1, cyl1, hole1).
    - All dimensions are in millimeters.
    - Cylinder height should be larger than the part depth when creating holes.
    - When positioning holes or cylinders, use TRANSLATE with x, y, z offsets.
    - For multiple subtractions, each hole must be a separate CREATE + TRANSLATE + SUBTRACT sequence.
    - The final command must always be EXPORT with a descriptive filename.
    - Do NOT include any comments, explanations, or extra text.
    - Output ONLY the DSL commands.

    Examples:

    User: Make a 30x20x10 box.
    Assistant:
    CREATE_BOX id=box1 width=30 height=20 depth=10
    EXPORT filename="box1.step"

    User: Make a 40x20x5 plate with a centered hole of radius 3.
    Assistant:
    CREATE_BOX id=plate width=40 height=20 depth=5
    CREATE_CYLINDER id=hole1 radius=3 height=10
    SUBTRACT target=plate tool=hole1
    EXPORT filename="plate_with_hole.step"

    User: Make a block 60x30x15 mm with two holes of radius 5 mm spaced 40 mm apart.
    Assistant:
    CREATE_BOX id=block width=60 height=30 depth=15
    CREATE_CYLINDER id=hole1 radius=5 height=20
    TRANSLATE id=hole1 x=-20 y=0 z=0
    CREATE_CYLINDER id=hole2 radius=5 height=20
    TRANSLATE id=hole2 x=20 y=0 z=0
    SUBTRACT target=block tool=hole1
    SUBTRACT target=block tool=hole2
    EXPORT filename="block_with_holes.step"

    User: Create a 50x50x10 square plate with four corner holes, radius 4mm, inset 8mm from edges.
    Assistant:
    CREATE_BOX id=plate width=50 height=50 depth=10
    CREATE_CYLINDER id=hole1 radius=4 height=15
    TRANSLATE id=hole1 x=-17 y=-17 z=0
    CREATE_CYLINDER id=hole2 radius=4 height=15
    TRANSLATE id=hole2 x=17 y=-17 z=0
    CREATE_CYLINDER id=hole3 radius=4 height=15
    TRANSLATE id=hole3 x=-17 y=17 z=0
    CREATE_CYLINDER id=hole4 radius=4 height=15
    TRANSLATE id=hole4 x=17 y=17 z=0
    SUBTRACT target=plate tool=hole1
    SUBTRACT target=plate tool=hole2
    SUBTRACT target=plate tool=hole3
    SUBTRACT target=plate tool=hole4
    EXPORT filename="plate_corner_holes.step"

    User: Make a cylinder radius 10 mm and height 30 mm with rounded edges.
    Assistant:
    CREATE_CYLINDER id=cyl1 radius=10 height=30
    FILLET id=cyl1 radius=2
    EXPORT filename="rounded_cylinder.step"

    User: Create a 100x50x20 base with a 30x30x40 tower centered on top.
    Assistant:
    CREATE_BOX id=base width=100 height=50 depth=20
    CREATE_BOX id=tower width=30 height=30 depth=40
    TRANSLATE id=tower x=0 y=0 z=30
    EXPORT filename="base_with_tower.step"

    User: Make a 80x40x12 plate with a slot 50mm long, 8mm wide through the center.
    Assistant:
    CREATE_BOX id=plate width=80 height=40 depth=12
    CREATE_BOX id=slot width=50 height=8 depth=20
    SUBTRACT target=plate tool=slot
    EXPORT filename="plate_with_slot.step"

    Now respond to the user's request with ONLY DSL commands.
    """
    prompt = system_prompt + "\nUser: " + user_prompt + "\nAssistant:\n"
    output = llm(prompt, max_tokens=300, stop=["User:", "\n\n"])
    return output["choices"][0]["text"].strip()

# --------------------------
# Full pipeline with validation & feedback
# --------------------------
def generate_part_from_text(user_prompt, output_dir="out", max_attempts=2):
    for attempt in range(max_attempts):
        print(f"\n💡 Attempt {attempt+1}: '{user_prompt}'")
        dsl = nl_to_dsl(user_prompt)
        print("📝 Generated DSL:\n", dsl)
        cmds = parse_dsl(dsl)
        valid, msg = validate_dsl(cmds)
        if valid:
            step_file = execute_dsl(cmds, output_dir=output_dir)
            print("✅ STEP file created at:", step_file)
            return step_file
        else:
            print("⚠️ DSL Validation Error:", msg)
            # Optionally, modify user_prompt to include error and retry
            user_prompt = f"{user_prompt}. Fix the following issue: {msg}"

    print("❌ Failed to generate valid CAD after retries")
    return None

# --------------------------
# Test
# --------------------------
if __name__ == "__main__":
    test_prompt = "Make a rectangular block 60x30x15 mm with two holes radius 5 mm spaced 40 mm apart."
    generate_part_from_text(test_prompt)