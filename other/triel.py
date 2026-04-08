from llama_cpp import Llama

llm = Llama(
    model_path="phi-3-mini.gguf",
    n_ctx=512,
    n_threads=6,   # adjust based on CPU
)

def classify_intent(text):
    prompt = f"""
    Classify into:
    [open_app, play_music, search_web, system_control, general_question]

    Only return one label.

    User: {text}
    Intent:
    """

    output = llm(prompt, max_tokens=5)
    return output["choices"][0]["text"].strip()