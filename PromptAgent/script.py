import pandas as pd
import google.generativeai as genai
import time
import random
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-1.5-pro"
genai.configure(api_key=API_KEY)
ai_model = genai.GenerativeModel(MODEL_NAME)

def generate_similar_prompts(example_prompt: str):
    prompt_instruction = f"""
    You are a prompt generation agent. 
    
    You need to generate 2 new prompts that are similar in style, intent, tone, 
    and question type, but phrased differently or exploring closely related ideas.
    
    Make sure it is formatted similarly and the tone, domain, and complexity 
    consistent with the example prompt below.

    Example prompt:
    "{example_prompt}"
    Output the new prompts as a clean numbered list, no extra commentary.
    """

    try:
        resp = ai_model.generate_content(prompt_instruction)
        content = resp.text.strip()
        new_prompts = []
        for line in content.splitlines():
            if line.strip():
                parts = line.split(". ", 1)
                if len(parts) > 1:
                    prompt = parts[-1].strip()
                else:
                    prompt = parts[0].strip()
                new_prompts.append(prompt)
        return new_prompts[:2]
    except Exception as e:
        print("Error", e)
        return

def main():
    df = pd.read_csv("example_prompts.csv")
    if "prompt" in df.columns:
        prompt_col = "prompt"
    else:
        possible_cols = []
        for c in df.columns:
            if "prompt" in c.lower():
                possible_cols.append(c)

        if possible_cols:
            prompt_col = possible_cols[0]
        else:
            prompt_col = None

    all_new_rows = []

    for i, row in df.iterrows():
        example_prompt = str(row[prompt_col]).strip()
        if not example_prompt:
            continue

        new_prompts = generate_similar_prompts(example_prompt)

        for new_p in new_prompts:
            new_row = row.copy()
            new_row[prompt_col] = new_p
            all_new_rows.append(new_row.to_dict())

    output_df = pd.DataFrame(all_new_rows)
    output_df.to_csv("output_prompts_df", index=False)

if __name__ == "__main__":
    main()
