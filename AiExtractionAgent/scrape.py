import os
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()
OPENAI_EMAIL = os.getenv("OPENAI_EMAIL")
OPENAI_PASSWORD = os.getenv("OPENAI_PASSWORD")
CLAUDE_EMAIL = os.getenv("CLAUDE_EMAIL")
CLAUDE_PASSWORD = os.getenv("CLAUDE_PASSWORD")
GEMINI_EMAIL = os.getenv("GEMINI_EMAIL")
GEMINI_PASSWORD = os.getenv("GEMINI_PASSWORD")

prompts_df = pd.read_csv("prompts.csv")
prompts = prompts_df["prompt"].tolist()

llms = {
    "Perplexity": "https://www.perplexity.ai/",
    "Grok": "https://x.ai/grok",
    "Claude": "https://www.anthropic.com/claude",
    "Gemini": "https://gemini.google.com/",
    "ChatGPT": "https://chat.openai.com/"
}

results = []

chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-notifications")
driver = webdriver.Chrome(service=Service(), options=chrome_options)
wait = WebDriverWait(driver, 20)

def login_chatgpt():
    driver.get("https://chat.openai.com/auth/login")
    wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(OPENAI_EMAIL)
    driver.find_element(By.NAME, "password").send_keys(OPENAI_PASSWORD + Keys.ENTER)
    time.sleep(5) 

def login_claude():
    driver.get("https://www.anthropic.com/login")
    wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(CLAUDE_EMAIL)
    driver.find_element(By.NAME, "password").send_keys(CLAUDE_PASSWORD + Keys.ENTER)
    time.sleep(5)

def login_gemini():
    driver.get("https://gemini.google.com/")
    wait.until(EC.presence_of_element_located((By.ID, "identifierId"))).send_keys(GEMINI_EMAIL + Keys.ENTER)
    time.sleep(3)
    wait.until(EC.presence_of_element_located((By.NAME, "password"))).send_keys(GEMINI_PASSWORD + Keys.ENTER)
    time.sleep(5)

def extract_response(llm, prompt):
    driver.get(llms[llm])
    time.sleep(5)
    
    try:
        if llm == "Perplexity":
            input_box = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
            input_box.clear()
            input_box.send_keys(prompt + Keys.ENTER)
            time.sleep(5)
            answer = driver.find_element(By.CSS_SELECTOR, "div[data-testid='answer-text']").text
            
        elif llm == "Grok":
            input_box = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
            input_box.clear()
            input_box.send_keys(prompt + Keys.ENTER)
            time.sleep(5)
            answer = driver.find_element(By.CSS_SELECTOR, "div.reply").text
            
        elif llm == "Claude":
            input_box = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
            input_box.clear()
            input_box.send_keys(prompt + Keys.ENTER)
            time.sleep(5)
            answer = driver.find_element(By.CSS_SELECTOR, "div.response").text
            
        elif llm == "Gemini":
            input_box = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
            input_box.clear()
            input_box.send_keys(prompt + Keys.ENTER)
            time.sleep(5)
            answer = driver.find_element(By.CSS_SELECTOR, "div.output").text
            
        elif llm == "ChatGPT":
            input_box = wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
            input_box.clear()
            input_box.send_keys(prompt + Keys.ENTER)
            time.sleep(5)
            answer = driver.find_element(By.CSS_SELECTOR, "div.text-base").text
            
        results.append({"engine": llm, "prompt": prompt, "answer": answer})
    except Exception as e:
        print("Error", e)
        results.append({"engine": llm, "prompt": prompt, "answer": None})

login_chatgpt()
login_claude()
login_gemini()

for llm in llms:
    for prompt in prompts:
        extract_response(llm, prompt)

driver.quit()
df = pd.DataFrame(results)
df.to_csv("ai_responses_with_login.csv", index=False)
print("Results saved to csv")
