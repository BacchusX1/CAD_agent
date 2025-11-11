from llama_cpp import Llama

model_path = "/home/bacchus/.cache/huggingface/hub/models--TheBloke--Mistral-7B-Instruct-v0.2-GGUF/snapshots/3a6fbf4a41a1d52e415a4958cde6856d34b2db93/mistral-7b-instruct-v0.2.Q4_K_M.gguf"

llm = Llama(model_path=model_path, n_ctx=2048, n_threads=8)

prompt = "You are a helpful assistant. What is 3 + 4?"

output = llm(prompt, max_tokens=500, stop=["</s>"])
print(output["choices"][0]["text"])