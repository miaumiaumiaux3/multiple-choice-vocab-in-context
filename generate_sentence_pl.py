#############################################
# Bielik-7B-Instruct-v0.1-GPTQ
# https://colab.research.google.com/drive/1Al9glPVCuOXbtDsks8cMcuzkuu8YDzpg?usp=sharing#scrollTo=Jr2DiK6PLHdQ
#
# Required installs and dependencies:
# pip install optimum -q
# pip install auto-gptq -q
# pip install ctransformers[cuda]
######################################

import torch
import warnings

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


def load_model():
    model_id = "speakleash/Bielik-7B-Instruct-v0.1-GPTQ"
    tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto",
        trust_remote_code=False,
        revision="main"
    )
    pipe = pipeline(model=model, tokenizer=tokenizer, task='text-generation', return_full_text=False)
    gptq = True #should this be global?

    return pipe

def prompt_model(pipe, human_prompt, t = 120) -> str:
    prompt = f"<s>[INST]{human_prompt}[/INST]"
    outputs = pipe(
        prompt,
        max_new_tokens=t,
        do_sample=True,
        temperature=0.1, #0.1 is the default, changing it to .5 leads to... German xD
        top_p=0.95,
    )
    return outputs[0]["generated_text"]

def generate_sample_sentence(pipe, word):
    built_prompt = f"Napisz zdanie, w którym pojawia się słowo {word}."
    result = prompt_model(pipe, built_prompt)
    return result


#For running as a solo script to play with a model
if __name__ == "__main__":
    warnings.filterwarnings("ignore") #suppress warnings, since the output gets MESSY, comment out to debug issues

    print(f"CUDA is available: {torch.cuda.is_available()}")
    print(f"CUDA device count: {torch.cuda.device_count()}")
    print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
    print(f"CUDA device index: {torch.cuda.current_device()}")
    print(f"CUDA device: {torch.cuda.get_device_properties(0)}")
    print(f"PyTorch version: {torch.__version__}")
    print("------------------------------------------------------------")

    pipe = load_polish_model()
    gptq = True

    while True:
        human_prompt = input("Enter a prompt:\n")
        if human_prompt.lower() == "exit":
            exit()
        if not human_prompt:
            print("You wrote nothing, so I'm assuming you're done for now, goodbye!")
            exit()
        result = prompt_polish_model(pipe, human_prompt)
        print(result)