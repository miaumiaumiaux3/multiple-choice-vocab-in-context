###################
# https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF
# Required downloads and dependencies
# pip3 install huggingface-hub
# pip install llama-cpp-python
# huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF mistral-7b-instruct-v0.2.Q4_K_M.gguf --local-dir . --local-dir-use-symlinks False
#################

from llama_cpp import Llama

def load_model():
    llm = Llama(
        model_path="./mistral-7b-instruct-v0.2.Q4_K_M.gguf",  # Download the model file first
        #chat_format= "llama-2", # The chat format to use - either "llama-1" or "llama-2" -- CAN BE OMITTED FOR DEFAULT FLAVOR
        n_ctx=32768,  # The max sequence length to use - note that longer sequence lengths require much more resources
        n_threads=8,            # The number of CPU threads to use, tailor to your system and the resulting performance
        n_gpu_layers=35         # The number of layers to offload to GPU, if you have GPU acceleration available
    )
    return llm

def prompt_model(llm, human_prompt, t = 120) -> str:
    output = llm(
        f"<s>[INST] {human_prompt} [/INST]", # Prompt
        max_tokens=t,  # Generate up to 120 tokens
        stop=["</s>"],   # Example stop token - not necessarily correct for this specific model! Please check before using.
        echo=False        # Whether to echo the prompt
    )
    return(output["choices"][0]["text"])

def generate_sample_sentence(llm, word):
    built_prompt = f"Write a sentence that contains the word {word}."
    result = prompt_model(llm, built_prompt)
    return result

#For running as a solo script to play with a model
if __name__ == "__main__":
    # print(f"CUDA is available: {torch.cuda.is_available()}")
    # print(f"CUDA device count: {torch.cuda.device_count()}")
    # print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
    # print(f"CUDA device index: {torch.cuda.current_device()}")
    # print(f"CUDA device: {torch.cuda.get_device_properties(0)}")
    # print(f"PyTorch version: {torch.__version__}")
    print("------------------------------------------------------------")

    llm = load_model()

    while True:
        human_prompt = input("Enter a prompt:\n")
        if human_prompt.lower() == "exit":
            exit()
        if not human_prompt:
            print("You wrote nothing, so I'm assuming you're done for now, goodbye!")
            exit()
        result = prompt_model(llm, human_prompt)
        print(result)