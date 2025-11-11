from llama_cpp import Llama

model_path = "/home/bacchus/.cache/huggingface/hub/models--TheBloke--Mistral-7B-Instruct-v0.2-GGUF/snapshots/3a6fbf4a41a1d52e415a4958cde6856d34b2db93/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
llm = Llama(model_path=model_path, n_ctx=2048, n_threads=8)

# The DSL description and examples
system_prompt = """
You are a CAD design assistant. 
You receive a natural language request describing a simple 3D shape.
You must output only valid DSL commands that follow this grammar:

Commands:
CREATE_BOX id=<id> width=<float> height=<float> depth=<float>
CREATE_CYLINDER id=<id> radius=<float> height=<float>
TRANSLATE id=<id> x=<float> y=<float> z=<float>
SUBTRACT target=<id> tool=<id>
FILLET id=<id> radius=<float>
EXPORT filename="<filename>"

Rules:
- Use only the commands above.
- Each command is on its own line.
- Always include an EXPORT command at the end.
- Use millimeters.
- No comments or explanations.
- Start each new solid with a CREATE_* command.

Examples:
User: Make a 30x20x10 box.
Assistant:
CREATE_BOX id=box1 width=30 height=20 depth=10
EXPORT filename="box.step"

User: Make a 40x20x5 plate with a centered hole of radius 3.
Assistant:
CREATE_BOX id=plate width=40 height=20 depth=5
CREATE_CYLINDER id=hole1 radius=3 height=10
SUBTRACT target=plate tool=hole1
EXPORT filename="plate_with_hole.step"
"""

# Test user request
user_prompt = "Make a rectangular block 60x30x15 mm with two holes radius 5 mm spaced 40 mm apart."

prompt = system_prompt + "\nUser: " + user_prompt + "\nAssistant:\n"

output = llm(prompt, max_tokens=200, stop=["User:", "\n\n"])
print(output["choices"][0]["text"].strip())
