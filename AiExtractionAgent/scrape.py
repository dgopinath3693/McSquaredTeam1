import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime

class AIExtractionAgent:
    def __init__(self, prompts_csv="output_prompts_df.csv", output_csv="ai_responses_extracted.csv"):
        self.prompts_csv = prompts_csv
        self.output_csv = output_csv
        self.results = []
        self.driver = None
        self.wait = None
        self.llms = {
            "Perplexity": "https://www.perplexity.ai/",
            "ChatGPT": "https://chatgpt.com/",
            "Copilot": "https://copilot.microsoft.com/",
            "Gemini": "https://gemini.google.com/app"
        }
        self.load_prompts()

    def load_prompts(self):
        try:
            self.prompts_df = pd.read_csv(self.prompts_csv)
            self.prompts = self.prompts_df["Prompt Text"].tolist()
        except Exception:
            raise

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        self.driver = webdriver.Chrome(service=Service(), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)

    def wait_for_response_completion(self, llm, max_wait=60):
        wait_times = {
            "ChatGPT": 12,
            "Perplexity": 20,
            "Copilot": 15,
            "Gemini": 12
        }
        time.sleep(wait_times.get(llm, 10))
        return True

    def extract_perplexity(self, prompt):
        try:
            time.sleep(3)
            input_box = None
            input_selectors = [
                "textarea[placeholder*='Ask']",
                "textarea[placeholder*='anything']",
                "textarea",
                "div[contenteditable='true']"
            ]
            for selector in input_selectors:
                try:
                    input_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if input_box:
                        break
                except:
                    continue
            if not input_box:
                return "Could not find input box"
            input_box.click()
            time.sleep(1)
            try:
                input_box.clear()
            except:
                input_box.send_keys(Keys.COMMAND + "a")
                input_box.send_keys(Keys.DELETE)
            input_box.send_keys(prompt)
            time.sleep(1)
            submitted = False
            try:
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='Submit'], button[type='submit']")
                submit_button.click()
                submitted = True
            except:
                input_box.send_keys(Keys.ENTER)
                submitted = True
            if not submitted:
                return "Could not submit prompt"
            time.sleep(25)
            best_answer = ""
            answer_selectors = [
                "div[class*='answer-container']",
                "div[class*='Answer-module']",
                "div[data-testid='answer']",
                "div.prose.dark\\:prose-invert",
            ]
            for selector in answer_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        answer = elem.text.strip()
                        bad_phrases = [
                            "Working…", "Ask a follow-up", "Sign in", "create an account",
                            "Unlock Pro", "Continue with", "Single sign-on", "Answer\n"
                        ]
                        is_bad = any(phrase in answer for phrase in bad_phrases)
                        if (answer and not is_bad and len(answer) > len(best_answer) and
                            len(answer) > 100 and prompt[:50].lower() not in answer.lower()):
                            best_answer = answer
                except Exception:
                    continue
            if best_answer:
                return self._clean_answer(best_answer)
            try:
                paragraphs = self.driver.find_elements(By.CSS_SELECTOR, "div.prose p, div[class*='answer'] p")
                combined = "\n\n".join([p.text.strip() for p in paragraphs if len(p.text.strip()) > 50])
                if combined and len(combined) > 100:
                    return self._clean_answer(combined)
            except:
                pass
            try:
                main = self.driver.find_element(By.TAG_NAME, "main")
                answer = main.text.strip()
                answer = self._clean_answer(answer)
                if answer and len(answer) > 100:
                    return answer
            except:
                pass
        except Exception:
            pass
        return "Could not extract answer"

    def _clean_answer(self, text):
        if not text:
            return text
        noise_patterns = [
            "Working…",
            "Ask a follow-up",
            "Sign in or create an account",
            "Unlock Pro Search and History",
            "Continue with Google",
            "Continue with Apple",
            "Continue with email",
            "Single sign-on (SSO)",
            "Answer\n",
        ]
        for noise in noise_patterns:
            text = text.replace(noise, "")
        lines = text.split('\n')
        cleaned_lines = []
        skip_count = 0
        for line in lines:
            if skip_count < 3 and len(line.strip()) < 30:
                skip_count += 1
                continue
            if line.strip():
                cleaned_lines.append(line.strip())
        return '\n'.join(cleaned_lines).strip()

    def extract_chatgpt(self, prompt):
        try:
            input_box = self.wait.until(EC.presence_of_element_located((By.ID, "prompt-textarea")))
            input_box.clear()
            input_box.send_keys(prompt)
            send_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='send-button']")
            send_button.click()
        except:
            try:
                input_box = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
                input_box.clear()
                input_box.send_keys(prompt)
                input_box.send_keys(Keys.ENTER)
            except Exception:
                return "Could not send prompt"
        self.wait_for_response_completion("ChatGPT")
        selectors = [
            "div[data-message-author-role='assistant']",
            "div.markdown",
            "div[class*='agent-turn']",
            "div[class*='response']"
        ]
        for selector in selectors:
            try:
                answer_elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if answer_elems:
                    answer = answer_elems[-1].text
                    if answer and len(answer) > 10:
                        return answer
            except NoSuchElementException:
                continue
        return "Could not extract answer"

    def extract_copilot(self, prompt):
        try:
            time.sleep(3)
            input_selectors = [
                "textarea[placeholder*='Ask']",
                "textarea.input",
                "div[contenteditable='true']",
                "textarea[id*='search']",
                "textarea"
            ]
            input_box = None
            for selector in input_selectors:
                try:
                    input_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if input_box:
                        break
                except:
                    continue
            if not input_box:
                return "Could not find input box"
            input_box.click()
            time.sleep(1)
            try:
                input_box.clear()
            except:
                input_box.send_keys(Keys.COMMAND + "a")
                input_box.send_keys(Keys.DELETE)
            input_box.send_keys(prompt)
            time.sleep(1)
            submitted = False
            send_selectors = [
                "button[aria-label*='Submit']",
                "button[aria-label*='Send']",
                "button[type='submit']",
                "button[class*='submit']"
            ]
            for selector in send_selectors:
                try:
                    send_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if send_button.is_enabled():
                        send_button.click()
                        submitted = True
                        break
                except:
                    continue
            if not submitted:
                input_box.send_keys(Keys.ENTER)
                submitted = True
            if not submitted:
                return "Could not submit prompt"
            time.sleep(20)
            try:
                time.sleep(5)
            except:
                pass
            selectors = [
                "cib-message[type='text'][source='bot']",
                "cib-message-group[source='bot'] cib-message",
                "cib-message[type='text']",
                "div[class*='ac-textBlock']",
                "div.ac-textBlock",
                "div[class*='response']",
                "div[class*='answer']",
                "div[class*='message'][class*='bot']",
                "div[class*='markdown']",
                "div.prose",
            ]
            best_answer = ""
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in reversed(elements):
                        answer = elem.text.strip()
                        if (answer and len(answer) > len(best_answer) and len(answer) > 50 and
                            prompt[:50].lower() not in answer.lower()):
                            best_answer = answer
                except:
                    continue
            if best_answer:
                return best_answer
            try:
                script = """
                let messages = document.querySelectorAll('cib-message');
                let result = '';
                messages.forEach(msg => {
                    if (msg.getAttribute('source') === 'bot') {
                        result += msg.textContent + '\\n';
                    }
                });
                return result.trim();
                """
                answer = self.driver.execute_script(script)
                if answer and len(answer) > 100:
                    return answer
            except Exception:
                pass
            try:
                main = self.driver.find_element(By.CSS_SELECTOR, "main, #b_sydConvCont, cib-serp")
                answer = main.text.strip()
                if answer and len(answer) > 100:
                    answer = self._clean_copilot_answer(answer, prompt)
                    return answer
            except:
                pass
        except Exception:
            pass
        return "Could not extract answer"

    def _clean_copilot_answer(self, text, prompt):
        if not text:
            return text
        text = text.replace("Today\nYou said\n", "")
        text = text.replace("You said\n", "")
        text = text.replace("Today\n", "")
        prompt_preview = prompt[:100]
        if prompt_preview in text[:300]:
            idx = text.find(prompt_preview)
            if idx >= 0:
                remaining = text[idx + len(prompt_preview):].strip()
                lines = remaining.split('\n')
                cleaned_lines = []
                for i, line in enumerate(lines):
                    if i > 0 or len(line) > 200 or any(marker in line for marker in ["Copilot", "I cannot", "Based on", "According to"]):
                        cleaned_lines.append(line)
                text = '\n'.join(cleaned_lines).strip()
        return text

    def extract_gemini(self, prompt):
        try:
            time.sleep(3)
            input_selectors = [
                "rich-textarea[placeholder*='Enter']",
                "div[contenteditable='true'][aria-label*='prompt']",
                "div.ql-editor[contenteditable='true']",
                "div[contenteditable='true']",
                "textarea"
            ]
            input_box = None
            for selector in input_selectors:
                try:
                    input_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if input_box:
                        break
                except:
                    continue
            if not input_box:
                return "Could not find input box"
            input_box.click()
            time.sleep(1)
            try:
                input_box.clear()
            except:
                input_box.send_keys(Keys.COMMAND + "a")
                input_box.send_keys(Keys.DELETE)
                time.sleep(0.5)
            input_box.send_keys(prompt)
            time.sleep(1)
            submitted = False
            send_selectors = [
                "button[aria-label*='Send']",
                "button[mattooltip*='Send']",
                "button[class*='send']",
                "button[type='submit']",
            ]
            for selector in send_selectors:
                try:
                    send_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if send_button.is_enabled():
                        send_button.click()
                        submitted = True
                        break
                except:
                    continue
            if not submitted:
                try:
                    input_box.send_keys(Keys.ENTER)
                    submitted = True
                except:
                    pass
            if not submitted:
                return "Could not submit prompt"
            time.sleep(12)
            time.sleep(3)
            selectors = [
                "message-content[class*='model-response']",
                "model-response .markdown",
                "div[class*='model-response']",
                "div[class*='response-container']",
                "div.markdown",
                "message-content",
                "div[class*='message'][class*='model']",
            ]
            best_answer = ""
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in reversed(elements):
                        answer = elem.text.strip()
                        if (answer and len(answer) > len(best_answer) and len(answer) > 50 and
                            prompt[:50].lower() not in answer.lower()):
                            best_answer = answer
                except:
                    continue
            if best_answer:
                return best_answer
            try:
                main = self.driver.find_element(By.TAG_NAME, "main")
                answer = main.text.strip()
                if answer and len(answer) > 100:
                    if prompt[:50] in answer[:300]:
                        parts = answer.split(prompt[:50], 1)
                        if len(parts) > 1:
                            answer = parts[1].strip()
                    if answer and len(answer) > 100:
                        return answer
            except:
                pass
        except Exception:
            pass
        return "Could not extract answer"

    def extract_response(self, llm, prompt, prompt_index, retry_count=0, max_retries=2):
        try:
            self.driver.get(self.llms[llm])
            time.sleep(3)
            if llm == "Perplexity":
                answer = self.extract_perplexity(prompt)
            elif llm == "ChatGPT":
                answer = self.extract_chatgpt(prompt)
            elif llm == "Copilot":
                answer = self.extract_copilot(prompt)
            elif llm == "Gemini":
                answer = self.extract_gemini(prompt)
            else:
                answer = "Unknown LLM"
            if (answer and answer != "Could not extract answer" and
                answer != "Could not send prompt" and answer != "Could not find input box"):
                status = "success"
            else:
                status = "failed"
            if status == "failed" and retry_count < max_retries:
                time.sleep(5)
                return self.extract_response(llm, prompt, prompt_index, retry_count + 1, max_retries)
            self.results.append({
                "llm": llm,
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "full_prompt": prompt,
                "answer": answer,
                "answer_length": len(answer) if answer else 0,
                "status": status,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except TimeoutException:
            self.results.append({
                "llm": llm,
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "full_prompt": prompt,
                "answer": None,
                "answer_length": 0,
                "status": "timeout",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception:
            self.results.append({
                "llm": llm,
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "full_prompt": prompt,
                "answer": None,
                "answer_length": 0,
                "status": "error",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

    def save_progress(self):
        if self.results:
            df = pd.DataFrame(self.results)
            df.to_csv(self.output_csv, index=False)

    def run(self, llm_subset=None, prompt_limit=None):
        try:
            self.setup_driver()
            llms_to_process = llm_subset if llm_subset else list(self.llms.keys())
            prompts_to_process = self.prompts[:prompt_limit] if prompt_limit else self.prompts
            for llm in llms_to_process:
                for idx, prompt in enumerate(prompts_to_process):
                    self.extract_response(llm, prompt, idx)
                    if (idx + 1) % 5 == 0:
                        self.save_progress()
                    if idx < len(prompts_to_process) - 1:
                        time.sleep(5)
                if llm != llms_to_process[-1]:
                    time.sleep(15)
        finally:
            if self.driver:
                self.driver.quit()
            self.save_progress()
            self.print_summary()

    def print_summary(self):
        if not self.results:
            return
        df = pd.DataFrame(self.results)
        print("\n" + "="*60)
        print("EXTRACTION SUMMARY")
        print("="*60)
        print(f"Total responses attempted: {len(self.results)}")
        print(f"Successful: {len(df[df['status'] == 'success'])}")
        print(f"Failed: {len(df[df['status'] == 'failed'])}")
        print(f"Timeout: {len(df[df['status'] == 'timeout'])}")
        print(f"Errors: {len(df[df['status'] == 'error'])}")
        print(f"\nBreakdown by LLM:")
        for llm in df['llm'].unique():
            llm_df = df[df['llm'] == llm]
            success_rate = len(llm_df[llm_df['status'] == 'success']) / len(llm_df) * 100
            print(f"  {llm}: {success_rate:.1f}% success rate")
        print(f"\nResults saved to: {self.output_csv}")
        print("="*60)


if __name__ == "__main__":
    agent = AIExtractionAgent()
    agent.run(prompt_limit=1)
