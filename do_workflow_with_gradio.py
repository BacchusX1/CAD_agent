from natural_languange_to_CAD import generate_part_from_text
import cadquery as cq
import gradio as gr
import tempfile
import os
import base64

OUTPUT_DIR = "out"


def generate_step_file(nl_prompt):
    """Generate a STEP file from the NL prompt and return the path.

    Returns (step_file_path or None)
    """
    step_file = generate_part_from_text(nl_prompt, output_dir=OUTPUT_DIR)
    return step_file


def load_preview_from_step(step_file_path):
    """Load a STEP file, export to STL, and return an iframe HTML (srcdoc) with Three.js viewer.

    Returns an HTML string safe for Gradio's HTML component.
    """
    if not step_file_path or not os.path.exists(step_file_path):
        return "<div style='padding:16px;color:#ddd;background:#111'>No STEP file available. Generate a part first.</div>"

    try:
        part = cq.importers.importStep(step_file_path)
    except Exception as e:
        return f"<div style='padding:16px;color:#ddd;background:#111'>Failed to import STEP: {str(e)}</div>"

    # Export to temporary STL file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as tmp_stl:
            stl_file = tmp_stl.name
        cq.exporters.export(part, stl_file)

        with open(stl_file, "rb") as f:
            stl_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        return f"<div style='padding:16px;color:#ddd;background:#111'>Failed to export STL: {str(e)}</div>"
    finally:
        try:
            if os.path.exists(stl_file):
                os.remove(stl_file)
        except Exception:
            pass

    # Build improved viewer HTML
    inner_html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <style>html,body{{height:100%;margin:0;background:#111;color:#fff}}#viewer{{width:100%;height:100%;}}</style>
    </head>
    <body>
      <div id="viewer">Loading preview...</div>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r148/three.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/three@0.148.0/examples/js/loaders/STLLoader.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/three@0.148.0/examples/js/controls/OrbitControls.js"></script>
      <script>
      (function(){{
        const container = document.getElementById('viewer');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x202124);

        const camera = new THREE.PerspectiveCamera(50, container.clientWidth/container.clientHeight, 0.1, 10000);
        const renderer = new THREE.WebGLRenderer({antialias:true});
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio || 1);
        container.innerHTML = '';
        container.appendChild(renderer.domElement);

        const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 0.6);
        scene.add(hemi);
        const dir = new THREE.DirectionalLight(0xffffff, 0.8);
        dir.position.set(5,10,7.5);
        scene.add(dir);

        const loader = new THREE.STLLoader();
        const bytes = Uint8Array.from(atob("{stl_b64}"), c => c.charCodeAt(0));
        const geometry = loader.parse(bytes.buffer);

        // compute center and fit camera
        geometry.computeBoundingBox();
        const center = new THREE.Vector3();
        geometry.boundingBox.getCenter(center);
        const size = geometry.boundingBox.getSize(new THREE.Vector3()).length();

        const material = new THREE.MeshStandardMaterial({color:0x9db3c9, metalness:0.2, roughness:0.4});
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.sub(center);
        scene.add(mesh);

        camera.position.copy(new THREE.Vector3(0, 0, size * 2.0));
        camera.lookAt(new THREE.Vector3(0,0,0));

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.target.set(0,0,0);
        controls.update();

        function onWindowResize(){{
          camera.aspect = container.clientWidth / container.clientHeight;
          camera.updateProjectionMatrix();
          renderer.setSize(container.clientWidth, container.clientHeight);
        }}
        window.addEventListener('resize', onWindowResize);

        function animate(){{
          requestAnimationFrame(animate);
          controls.update();
          renderer.render(scene, camera);
        }}
        animate();
      }})();
      </script>
    </body>
    </html>
    """

    iframe_srcdoc = inner_html.replace('"', '&quot;')
    iframe_html = f"<iframe srcdoc=\"{iframe_srcdoc}\" style=\"width:100%;height:60vh;border:0;border-radius:6px;overflow:hidden;\"></iframe>"

    return iframe_html


def make_ui():
    with gr.Blocks(title="NL → CAD Generator with BRep Preview") as demo:
        gr.Markdown("""# NL → CAD Generator with BRep Preview
Type a natural language description of a part, get a STEP file and load the 3D preview on demand.
""")

        with gr.Row():
            nl = gr.Textbox(lines=3, placeholder="Describe your CAD part here...", label="nl_prompt")
            with gr.Column():
                step_file_out = gr.File(label="Download STEP")
                load_btn = gr.Button("Load Preview")
                html_out = gr.HTML(label="3D Preview")

        state = gr.State(value=None)

        def on_submit(prompt):
            step = generate_step_file(prompt)
            if not step:
                return None, None
            # return file path for download and keep step path in state
            return step, step

        submit_btn = gr.Button("Submit", variant="primary")
        clear_btn = gr.Button("Clear")

        submit_btn.click(on_submit, inputs=[nl], outputs=[step_file_out, state])

        def on_clear():
            return "", None, "<div style='padding:12px;color:#ddd;background:#111'>Preview cleared.</div>"

        clear_btn.click(on_clear, inputs=None, outputs=[nl, state, html_out])

        # Load preview from stored step path
        load_btn.click(lambda s: load_preview_from_step(s), inputs=[state], outputs=[html_out])

    return demo


if __name__ == "__main__":
    demo = make_ui()
    demo.launch(share=True)
