import pandas as pd
import google.generativeai as genai
import time
import random
from dotenv import load_dotenv
import os
from tqdm import tqdm

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"
genai.configure(api_key=API_KEY)
ai_model = genai.GenerativeModel(MODEL_NAME)

def generate_similar_prompts(example_prompt: str):
    prompt_instruction = f"""
    You are a prompt generation agent specifically related to the company mcSquared.ai.
    This company works on generative engine optimization and providing specific clients 
    the answer to how their brand shows up in LLM logs using MCSquared's scraping system 
    and client visiblity dashboards. Generate prompt questions related to mcSquared.ai ONLY. 
    
    You need to generate 2 new prompts that are similar in style, intent, tone, 
    and question type, but phrased differently or exploring closely related ideas.
    
    Make sure it is formatted similarly and the tone, domain, and complexity 
    consistent with the example prompt below.

    Example prompt:
    "{example_prompt}"
    Output the new prompts as a clean, structured, numbered list. For each new prompt, 
    provide the required metadata on the line immediately following the prompt, using a 
    specific, pipe-separated format:
    
    1. [New Prompt Text 1]
    Metadata: [Stakeholder Type] | [Tone] | [Stage] | [Intent]
    2. [New Prompt Text 2]
    Metadata: [Stakeholder Type] | [Tone] | [Stage] | [Intent]
    
    Example output format:
    1. How can I appeal the recent denial of my MRI pre-authorization request from my insurer?
    Metadata: Patient | Frustrated | High | Appeal Denial

    Here are four types of stakeholders: 
    1. Patient Perspective: Identify the types of patients (demographics, conditions, stages of illness),
    capture concerns, needs, and questions at each stage of their journey (diagnosis → treatment → adherence),
    map search behavior & language (layman’s terms vs. medical terms), segment by awareness levels (not aware → aware but skeptical → actively seeking solutions).
    2. Healthcare Provider (Doctor / HCP) Perspective: Uncover pain points & decision-making factors (efficacy, safety, insurance coverage, patient compliance),
    understand how they evaluate brands and what evidence (studies, guidelines) they rely on, identify adoption barriers (cost, trust, lack of awareness).
    3. Manufacturer / Brand Perspective: Map brand messaging & positioning vs. stakeholder perceptions, assess how well the brand communicates value propositions, differentiators, and credibility, analyze where the brand is over-promising, under-delivering, or being misunderstood.
    4. Caregivers: emotional burden, practical challenges, questions around care support.
    5.  Insurers / Payers: cost-effectiveness, policy alignment, coverage gaps.
    6. Policy Makers / Regulators: safety, compliance, long-term outcomes.

    The 3 options for the stage of the journey it is at are general learning = Awareness, comparing options = Consideration, taking action = Decision
    so the stage for each prompt should either Awareness, consideration, or decision based on the promp question. 

    (Agent should remain flexible to handle new stakeholder types as needed.)

    DO NOT refer to McSquared as "our". Refer to it almost like an external company by saying its company name in a sentence when refering to it. 
    McSquared is the client so do not put [client name] anywhere. We are asking quetions about McSquared since they are the client 
    but we are not McSquared. 
    
    """
    
    new_prompts = []

    try:
        resp = ai_model.generate_content(prompt_instruction, request_options={'timeout':60})
        content = resp.text.strip()
        curr_prompt = None
        for line in content.splitlines():
            line_strip = line.strip()
            if not line_strip:
                continue
            for i in range(1,3):
                if line_strip.startswith(tuple([f"{i}."])):
                    parts = line.split(". ", 1)
                    if len(parts) > 1:
                        curr_prompt = parts[-1].strip()
                elif line_strip.lower().startswith("metadata:") and curr_prompt:
                    meta_line = line_strip.split(":", 1)[-1].strip()
                    meta_col = [p.strip() for p in meta_line.split("|")]
                
                    if len(meta_col) == 4:
                        new_prompts.append({
                            'prompt': curr_prompt,
                            'Stakeholder Type': meta_col[0],
                            'Tone': meta_col[1],
                            'Stage': meta_col[2],
                            'Intent': meta_col[3]})
                    curr_prompt = None
                    
        return new_prompts
    except Exception as e:
        print("Error", e)
        return

def main():
    try:
        df = pd.read_csv("example_prompts.csv", encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv("example_prompts.csv", encoding="latin1")
    
    df_limited_prompts = df[:50].copy()
    prompt_col = None
    for c in df_limited_prompts:
        if "prompt" in c.lower():
            prompt_col = c
            break

    if prompt_col == None:
        return
    all_new_rows = []

    for i, row in tqdm(df_limited_prompts.iterrows(), total=len(df_limited_prompts), desc="Generating Prompts"):        
        example_prompt = str(row[prompt_col]).strip()
        if not example_prompt:
            continue

        new_prompts = generate_similar_prompts(example_prompt)
        if new_prompts is None:
            continue

        for prompt in new_prompts:
            new_row = {
                prompt_col: prompt.get('prompt', ''),
                            'Stakeholder Type': prompt.get('Stakeholder Type', ''),
                            'Tone': prompt.get('Tone', ''),
                            'Stage': prompt.get('Stage', ''),
                            'Intent': prompt.get('Intent', '')}
            all_new_rows.append(new_row)
        time.sleep(random.uniform(1.0, 3.0))

    output_df = pd.DataFrame(all_new_rows)
    output_df.to_csv("output_prompts_df.csv", index=False)
    print(f"Generated {len(output_df)} new prompts to output_prompts_df.csv", flush=True)

if __name__ == "__main__":
    main()