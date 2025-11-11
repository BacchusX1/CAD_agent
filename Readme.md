
# CAD Agent — Natural language → CAD (DSL → STEP)

A compact pipeline that converts plain-English part descriptions into a small domain-specific language (DSL), validates it, executes it with CadQuery, and exports STEP files — with a tiny Gradio demo for previewing results.

## Project idea (short)

This project demonstrates a constrained, reliable way to use a local LLM as an interpreter: the LLM maps user text to an exact DSL (no extra prose). The repository focuses on the end-to-end flow:

- Natural language prompt → LLM → DSL commands
- DSL parser & validator → CadQuery executor
- Export STEP and preview in-browser using a Three.js/STL viewer inside a Gradio UI

The DSL is intentionally small (CREATE_BOX, CREATE_CYLINDER, TRANSLATE, SUBTRACT, FILLET, EXPORT) so the LLM's output can be validated and executed deterministically.

## Which LLM is used?

By default the project uses a local GGUF model loaded with `llama_cpp` (the `llama-cpp-python` package). The code points to a Mistral 7B Instruct GGUF snapshot by default:

- Model: TheBloke / Mistral-7B-Instruct (GGUF)
- Loader: `from llama_cpp import Llama` (see `natural_languange_to_CAD.py`)
- Default model path is set in `natural_languange_to_CAD.py` as `MODEL_PATH` — edit that constant to point to your downloaded GGUF file.

If you prefer remote APIs (OpenAI, Hugging Face inference, etc.), you can replace `nl_to_dsl()` with an API call and keep the same parsing/validation/execution pipeline.

## Quick start

1. Install the main dependencies (if you don't have a `requirements.txt`):

```bash
pip install cadquery gradio llama-cpp-python
```

2. Ensure you have a compatible GGUF model downloaded and update `MODEL_PATH` in `natural_languange_to_CAD.py`.

3. Run the Gradio demo:

```bash
python do_workflow_with_gradio.py
```

4. Or use the script directly (CLI test):

```bash
python natural_languange_to_CAD.py
# or
python natural_languange_to_CAD.py "Create a box 10x10x10"
```

Generated STEP files are written to the `out/` directory by default.

## Pipeline / architecture

- `nl_to_dsl(user_prompt)` — sends a system+user prompt to the LLM and expects ONLY DSL lines in the response.
- `parse_dsl()` — simple line-based parser producing a list of commands.
- `validate_dsl()` — checks IDs, numeric ranges, and references; returns error messages if invalid.
- `execute_dsl()` — builds CadQuery solids, applies transforms, performs boolean ops, and exports STEP via `cadquery.exporters`.
- `do_workflow_with_gradio.py` — wraps the pipeline in a Gradio UI to generate step from prompt and download it from browser/gradio 

## Screenshots

Prompt (input) in gradio browser page:

![Prompt screenshot](screenshots/prompt.png)

Result / step preview (Gradio):

![Result screenshot](screenshots/result_step.png)

## Where to look in the code

- `natural_languange_to_CAD.py` — LLM prompt, DSL parser/validator, CadQuery executor, and the default `MODEL_PATH`.
- `do_workflow_with_gradio.py` — Gradio UI to input prompt

## Next steps 

- Implement visualization in gradio

---
Updated: November 11, 2025

