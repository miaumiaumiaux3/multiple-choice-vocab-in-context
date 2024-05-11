#############################################
# Bielik-7B-Instruct-v0.1-GGUF
# https://colab.research.google.com/drive/1Al9glPVCuOXbtDsks8cMcuzkuu8YDzpg?usp=sharing#scrollTo=Jr2DiK6PLHdQ
#
# Required installs and dependencies:
# pip install optimum -q
# pip install auto-gptq -q
# pip install ctransformers[cuda]
######################################

import torch
import warnings

from ctransformers import AutoModelForCausalLM
from transformers import AutoTokenizer, pipeline


def load_model():
    model = AutoModelForCausalLM.from_pretrained(
        "speakleash/Bielik-7B-Instruct-v0.1-GGUF",
        model_file="bielik-7b-instruct-v0.1.Q4_K_M.gguf", # you can take different quantization resolution from speakleash/Bielik-7B-Instruct-v0.1-GGUF repo
        model_type="mistral", gpu_layers=50, hf=True
    )

    tokenizer = AutoTokenizer.from_pretrained(
        "speakleash/Bielik-7B-Instruct-v0.1", use_fast=True
    )

    pipe = pipeline(model=model, tokenizer=tokenizer, task='text-generation', return_full_text=False)

    return pipe

def prompt_model(pipe, human_prompt, temp=0.7, topp = 0.99) -> str:
    prompt = f"<s>[INST]{human_prompt}[/INST]"
    outputs = pipe(
        prompt,
        max_new_tokens=120,
        temperature=temp, #0.7 is mistral default, 0.1 was gptQchanging it to 0.5 has given German output
        do_sample=True, #gives more variety in the output versus greedy decoding
        top_p=topp, #top probability to sample from, default is 1, but 0.95 was reccommended in GPTQ setting
        # .99 is my current favorite
    )
    result = outputs[0]["generated_text"]
    return result.strip(' "\'\t\r\n')

def generate_sample_sentence(pipe, word):
    built_prompt = f"Napisz zdanie, które zawiera słowo {word}."
    #built_prompt = f"Napisz zaskakujące zdanie, które zawiera słowo {word}." #has interesting results, actually
    #built_prompt = f"Napisz kreatywne zdanie, które zawiera słowo {word}."
    #built_prompt = f"Napisz pierwsze zdanie opowieści, które zawiera słowo '{word}' i wprowadza poczucie tajemnicy."
    #built_prompt = f"Napisz pierwsze zdanie opowieści, które zawiera słowo '{word}' i wprowadza poczucie przygody."
    #built_prompt = f"Napisz pierwsze zdanie opowieści, które zawiera słowo '{word}' i wprowadza poczucie napięcia."
    #built_prompt = f"Napisz zdanie, w którym się pojawia słowo {word}."
    result = prompt_model(pipe, built_prompt)
    return result


#For running as a solo script to play with a model
if __name__ == "__main__":
    import time
    from datetime import timedelta

    warnings.filterwarnings("ignore") #suppress warnings, since the output gets MESSY, comment out to debug issues

    print(f"CUDA is available: {torch.cuda.is_available()}")
    print(f"CUDA device count: {torch.cuda.device_count()}")
    print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
    print(f"CUDA device index: {torch.cuda.current_device()}")
    print(f"CUDA device: {torch.cuda.get_device_properties(0)}")
    print(f"PyTorch version: {torch.__version__}")
    print(torch.backends.cudnn.version())
    print(torch.version.cuda)
    print("------------------------------------------------------------")

    pipe = load_model()

    # while True:
    #     #start timer
    #     start_time = time.monotonic()
    #     human_prompt = input("Enter a prompt:\n")
    #     if human_prompt.lower() == "exit":
    #         exit()
    #     if not human_prompt:
    #         print("You wrote nothing, so I'm assuming you're done for now, goodbye!")
    #         exit()
    #     result = prompt_model(pipe, human_prompt)
    #     print(result)
    #     #end timer
    #     end_time = time.monotonic()
    #     print('Runtime: ' + str(timedelta(seconds=end_time - start_time)))
    #


    while True:
        #start timer
        start_time = time.monotonic()
        human_prompt = "Napisz zdanie, które zawiera słowo taniec."
        #human_prompt = "Napisz zdanie, w którym znajduje się słowa tańczyć."
        #human_prompt = "Napisz zdanie, używając słowa tańczyć."
        result = prompt_model(pipe, human_prompt, temp=0.7, topp=.99)
        print(result)
        #end timer
        end_time = time.monotonic()
        print('Runtime: ' + str(timedelta(seconds=end_time - start_time)))



