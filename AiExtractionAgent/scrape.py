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
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API for summarization
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'extraction_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AIExtractionAgent:
    def __init__(self, prompts_csv=None, output_csv="ai_responses_extracted.csv"):
        # Default to PromptAgent folder if no path provided
        if prompts_csv is None:
            # Get the parent directory (McSquaredTeam1) and navigate to PromptAgent
            script_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(script_dir)
            prompts_csv = os.path.join(parent_dir, "PromptAgent", "output_prompts_df.csv")
        
        self.prompts_csv = prompts_csv
        self.output_csv = output_csv
        self.results = []
        self.driver = None
        self.wait = None
        
        # LLM endpoints
        # Note: Claude and Grok require login. Set skip_login_check=True to attempt anyway.
        self.llms = {
            "Perplexity": "https://www.perplexity.ai/",
            # "ChatGPT": "https://chatgpt.com/",
            # "Claude": "https://claude.ai/new",  # Requires login
            # "Grok": "https://x.com/i/grok",  # Requires X/Twitter login
            "Copilot": "https://copilot.microsoft.com/",
            "Gemini": "https://gemini.google.com/app"
        }
        
        # Load prompts
        self.load_prompts()
        
    def load_prompts(self):
        """Load prompts from CSV"""
        try:
            self.prompts_df = pd.read_csv(self.prompts_csv)
            self.prompts = self.prompts_df["Prompt Text"].tolist()
            logger.info(f"Loaded {len(self.prompts)} prompts from {self.prompts_csv}")
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
            raise
    
    def setup_driver(self):
        """Initialize Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(service=Service(), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        logger.info("Chrome driver initialized")
    
    def wait_for_response_completion(self, llm, max_wait=60):
        """Wait for LLM to complete its response"""
        wait_times = {
            "Claude": 15,
            "ChatGPT": 12,
            "Perplexity": 20,  # Increased because it searches the web
            "Grok": 12,
            "Copilot": 15,
            "Gemini": 12
        }
        time.sleep(wait_times.get(llm, 10))
        return True
    
    def summarize_text(self, text):
        """Summarize text using Gemini API"""
        if not GEMINI_API_KEY:
            logger.warning("Gemini API key not found - returning original text")
            return text
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            prompt = f"""Please provide a concise summary of the following text in 2-3 sentences:

{text}

Summary:"""
            
            response = model.generate_content(prompt)
            summary = response.text.strip()
            logger.info(f"Summarized {len(text)} chars to {len(summary)} chars")
            return summary
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return text  # Return original if summarization fails
    
    def debug_page_elements(self, llm_name):
        """Debug helper to log page elements when extraction fails"""
        try:
            logger.info(f"=== Debugging {llm_name} page ===")
            logger.info(f"Current URL: {self.driver.current_url}")
            
            # Check for textareas
            textareas = self.driver.find_elements(By.TAG_NAME, "textarea")
            logger.info(f"Found {len(textareas)} textarea elements")
            
            # Check for contenteditable divs
            editables = self.driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
            logger.info(f"Found {len(editables)} contenteditable elements")
            for i, elem in enumerate(editables[:3]):  # Log first 3
                try:
                    logger.info(f"  Editable {i}: visible={elem.is_displayed()}, size={elem.size}")
                except:
                    pass
            
            # Check page title
            logger.info(f"Page title: {self.driver.title}")
            logger.info("=== End debug ===")
        except Exception as e:
            logger.error(f"Debug failed: {e}")
    
    def extract_perplexity(self, prompt):
        """Extract response from Perplexity"""
        try:
            # Wait for page to fully load
            time.sleep(3)
            
            # Find textarea - updated selectors
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
                        logger.info(f"Found input using: {selector}")
                        break
                except:
                    continue
            
            if not input_box:
                return "Could not find input box"
            
            # Clear and send prompt
            input_box.click()
            time.sleep(1)
            
            # Try to clear - handle both textarea and contenteditable
            try:
                input_box.clear()
            except:
                input_box.send_keys(Keys.COMMAND + "a")
                input_box.send_keys(Keys.DELETE)
            
            input_box.send_keys(prompt)
            time.sleep(1)
            
            # Submit - try button first, then Enter
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
            
            # Wait for response - Perplexity searches the web so it takes longer
            logger.info("Waiting for Perplexity to search and generate response...")
            time.sleep(20)
            
            # Updated selectors for current Perplexity interface
            selectors = [
                "div[class*='prose'] > *",  # Get all prose content
                "div.prose",
                "div[class*='Answer']",
                "div[class*='answer']",
                "div[class*='result']",
                "div[class*='markdown']",
                "main div[class*='col'] > div > div",  # Layout structure
            ]
            
            best_answer = ""
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        answer = elem.text.strip()
                        # Filter out prompt, headers, and get substantial content
                        if (answer and 
                            len(answer) > len(best_answer) and 
                            len(answer) > 100 and 
                            prompt[:50].lower() not in answer.lower()):
                            best_answer = answer
                            logger.info(f"Found better answer ({len(answer)} chars) using: {selector}")
                except:
                    continue
            
            if best_answer:
                return best_answer
            
            # Fallback: get main content
            try:
                main = self.driver.find_element(By.TAG_NAME, "main")
                answer = main.text.strip()
                # Remove the prompt from the beginning if present
                if prompt[:50] in answer[:200]:
                    answer = answer[answer.find(prompt[:50]) + len(prompt[:50]):].strip()
                if answer and len(answer) > 100:
                    logger.info(f"Using main content ({len(answer)} chars)")
                    return answer
            except:
                pass
            
        except Exception as e:
            logger.error(f"Perplexity extraction error: {e}")
        
        return "Could not extract answer"
    
    def extract_chatgpt(self, prompt):
        """Extract response from ChatGPT"""
        try:
            # Try new interface first
            input_box = self.wait.until(EC.presence_of_element_located((By.ID, "prompt-textarea")))
            input_box.clear()
            input_box.send_keys(prompt)
            
            send_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='send-button']")
            send_button.click()
        except:
            # Fallback to alternative input method
            try:
                input_box = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "textarea")))
                input_box.clear()
                input_box.send_keys(prompt)
                input_box.send_keys(Keys.ENTER)
            except Exception as e:
                logger.error(f"Could not send prompt to ChatGPT: {e}")
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
    
    def extract_claude(self, prompt):
        """Extract response from Claude"""
        try:
            # Wait for page load - Claude.ai/new takes time
            logger.info("Waiting for Claude page to load...")
            time.sleep(5)
            
            # Check if redirected to login
            if "login" in self.driver.current_url.lower():
                logger.error("Claude requires login - redirected to login page")
                return "Login required - Claude.ai requires authentication"
            
            input_sent = False
            input_box = None
            
            # Try to find input field with multiple approaches - try each with fresh wait
            input_selectors = [
                ("fieldset div[contenteditable='true']", 10),
                ("div[contenteditable='true'][data-placeholder]", 10),
                ("div[contenteditable='true']", 10),
                ("div.ProseMirror[contenteditable='true']", 10),
                ("textarea", 5),
            ]
            
            for selector, wait_time in input_selectors:
                try:
                    logger.info(f"Trying Claude selector: {selector}")
                    temp_wait = WebDriverWait(self.driver, wait_time)
                    input_box = temp_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if input_box and input_box.is_displayed():
                        logger.info(f"Found Claude input using: {selector}")
                        break
                    else:
                        input_box = None
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not input_box:
                logger.error("Could not find Claude input field - trying one more time with any contenteditable")
                try:
                    # Last resort - find any contenteditable that's visible
                    all_editables = self.driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true']")
                    for elem in all_editables:
                        if elem.is_displayed() and elem.size['height'] > 20:
                            input_box = elem
                            logger.info("Found contenteditable element as fallback")
                            break
                except:
                    pass
            
            if not input_box:
                logger.error("Could not find Claude input field after all attempts")
                self.debug_page_elements("Claude")
                return "Could not find input box"
            
            # Click and focus
            input_box.click()
            time.sleep(1)
            
            # Clear any existing text
            try:
                input_box.clear()
            except:
                # For contenteditable divs
                input_box.send_keys(Keys.COMMAND + "a")
                input_box.send_keys(Keys.DELETE)
                time.sleep(0.5)
            
            # Type the prompt
            logger.info("Typing prompt into Claude...")
            input_box.send_keys(prompt)
            time.sleep(2)
            
            # Try to find and click send button - updated selectors
            send_selectors = [
                "button[aria-label*='Send']",
                "button[type='submit']",
                "button svg[data-icon='arrow-right']",
                "button:has(svg)",
            ]
            
            for selector in send_selectors:
                try:
                    logger.info(f"Looking for send button: {selector}")
                    send_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for send_button in send_buttons:
                        if send_button.is_displayed() and send_button.is_enabled():
                            send_button.click()
                            input_sent = True
                            logger.info(f"Clicked send button: {selector}")
                            break
                    if input_sent:
                        break
                except Exception as e:
                    logger.debug(f"Send button selector failed: {e}")
                    continue
            
            # Fallback: try keyboard shortcuts
            if not input_sent:
                try:
                    logger.info("Trying Enter key...")
                    input_box.send_keys(Keys.RETURN)
                    input_sent = True
                    logger.info("Sent via Enter key")
                except:
                    pass
            
            # Last resort: CMD+Enter or CTRL+Enter
            if not input_sent:
                try:
                    logger.info("Trying CMD+Enter...")
                    input_box.send_keys(Keys.COMMAND + Keys.RETURN)
                    input_sent = True
                    logger.info("Sent via CMD+Enter")
                except:
                    pass
            
            if not input_sent:
                logger.error("Could not send prompt to Claude")
                return "Could not send prompt"
            
            # Wait for Claude to respond
            logger.info("Waiting for Claude response...")
            time.sleep(15)
            
            # Additional wait for streaming to complete - look for indicators
            try:
                # Wait a bit more if we see streaming indicators
                time.sleep(5)
            except:
                pass
            
            # Try multiple response selectors
            best_answer = ""
            selectors = [
                "div[data-testid*='message'] div[class*='prose']",
                "div[class*='font-claude']",
                "div.font-claude-message",
                "div[class*='markdown']",
                "div.prose",
                "div[class*='prose']",
                "div[class*='message-content']",
                "div[class*='assistant'] > div",
            ]
            
            for selector in selectors:
                try:
                    answer_elems = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in reversed(answer_elems):  # Start from most recent
                        answer = elem.text.strip()
                        # Get longest substantial answer that's not the prompt
                        if (answer and 
                            len(answer) > len(best_answer) and 
                            len(answer) > 50 and 
                            prompt[:50].lower() not in answer.lower()):
                            best_answer = answer
                            logger.info(f"Found answer ({len(answer)} chars) using: {selector}")
                except:
                    continue
            
            if best_answer:
                return best_answer
            
            # Fallback: extract from main
            try:
                main = self.driver.find_element(By.TAG_NAME, "main")
                answer = main.text.strip()
                # Try to isolate the response from UI elements
                if answer and len(answer) > 100:
                    logger.info(f"Using main content ({len(answer)} chars)")
                    return answer
            except:
                pass
                
        except Exception as e:
            logger.error(f"Claude extraction error: {e}")
        
        return "Could not extract answer"
    
    def extract_grok(self, prompt):
        """Extract response from Grok (X.AI)"""
        try:
            # Wait for page load - Grok on X takes time
            logger.info("Waiting for Grok page to load...")
            time.sleep(6)
            
            # Check if redirected to login
            if "login" in self.driver.current_url.lower():
                logger.error("Grok requires login - redirected to X login page")
                return "Login required - Grok requires X/Twitter authentication"
            
            # Find input field - Grok uses X/Twitter interface
            input_selectors = [
                ("div[data-testid='dmComposerTextInput']", 10),  # X DM-style input
                ("div[contenteditable='true'][role='textbox']", 10),
                ("div[contenteditable='true'][data-testid]", 10),
                ("textarea[placeholder*='Ask']", 8),
                ("textarea[placeholder*='message']", 8),
                ("div[contenteditable='true']", 8),
                ("textarea", 5)
            ]
            
            input_box = None
            for selector, wait_time in input_selectors:
                try:
                    logger.info(f"Trying Grok selector: {selector}")
                    temp_wait = WebDriverWait(self.driver, wait_time)
                    input_box = temp_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if input_box and input_box.is_displayed():
                        logger.info(f"Found Grok input using: {selector}")
                        break
                    else:
                        input_box = None
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not input_box:
                logger.error("Could not find Grok input field - trying fallback")
                try:
                    # Find any visible contenteditable or textarea
                    all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true'], textarea")
                    for elem in all_inputs:
                        if elem.is_displayed() and elem.size['height'] > 20:
                            input_box = elem
                            logger.info("Found input element as fallback")
                            break
                except:
                    pass
            
            if not input_box:
                logger.error("Could not find Grok input field after all attempts")
                self.debug_page_elements("Grok")
                return "Could not find input box"
            
            # Send prompt
            logger.info("Clicking Grok input field...")
            input_box.click()
            time.sleep(1)
            
            # Clear existing content
            try:
                input_box.clear()
            except:
                input_box.send_keys(Keys.COMMAND + "a")
                input_box.send_keys(Keys.DELETE)
                time.sleep(0.5)
            
            logger.info("Typing prompt into Grok...")
            input_box.send_keys(prompt)
            time.sleep(2)
            
            # Submit - try multiple approaches
            submitted = False
            
            # Try to find send button
            send_selectors = [
                "button[data-testid='dmComposerSendButton']",  # X DM send button
                "button[aria-label*='Send']",
                "button[type='submit']",
                "button:has(svg[data-testid])",
            ]
            
            for selector in send_selectors:
                try:
                    logger.info(f"Looking for Grok send button: {selector}")
                    send_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in send_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            submitted = True
                            logger.info(f"Clicked send button: {selector}")
                            break
                    if submitted:
                        break
                except Exception as e:
                    logger.debug(f"Button selector failed: {e}")
                    continue
            
            # Fallback to keyboard
            if not submitted:
                try:
                    logger.info("Trying Enter key for Grok...")
                    input_box.send_keys(Keys.ENTER)
                    submitted = True
                    logger.info("Sent via Enter")
                except:
                    pass
            
            # Try CMD+Enter as last resort
            if not submitted:
                try:
                    logger.info("Trying CMD+Enter for Grok...")
                    input_box.send_keys(Keys.COMMAND + Keys.RETURN)
                    submitted = True
                    logger.info("Sent via CMD+Enter")
                except:
                    pass
            
            if not submitted:
                return "Could not submit prompt"
            
            # Wait for response
            logger.info("Waiting for Grok response...")
            time.sleep(12)
            
            # Try to find response
            selectors = [
                "div[data-testid*='message']",
                "div[class*='response']",
                "div[class*='answer']",
                "div[class*='message'][class*='assistant']",
                "div.prose",
                "article div",
            ]
            
            best_answer = ""
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in reversed(elements):
                        answer = elem.text.strip()
                        if (answer and 
                            len(answer) > len(best_answer) and 
                            len(answer) > 50 and 
                            prompt[:50].lower() not in answer.lower()):
                            best_answer = answer
                            logger.info(f"Found answer ({len(answer)} chars) using: {selector}")
                except:
                    continue
            
            if best_answer:
                return best_answer
            
            # Fallback
            try:
                main = self.driver.find_element(By.TAG_NAME, "main")
                answer = main.text.strip()
                if answer and len(answer) > 100:
                    return answer
            except:
                pass
                
        except Exception as e:
            logger.error(f"Grok extraction error: {e}")
        
        return "Could not extract answer"
    
    def extract_copilot(self, prompt):
        """Extract response from Microsoft Copilot"""
        try:
            # Wait for page load
            time.sleep(3)
            
            # Find input field
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
                        logger.info(f"Found Copilot input using: {selector}")
                        break
                except:
                    continue
            
            if not input_box:
                return "Could not find input box"
            
            # Send prompt
            input_box.click()
            time.sleep(1)
            
            try:
                input_box.clear()
            except:
                input_box.send_keys(Keys.COMMAND + "a")
                input_box.send_keys(Keys.DELETE)
            
            input_box.send_keys(prompt)
            time.sleep(1)
            
            # Submit - Copilot often uses a send button
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
                        logger.info(f"Clicked send button: {selector}")
                        break
                except:
                    continue
            
            if not submitted:
                input_box.send_keys(Keys.ENTER)
                submitted = True
            
            if not submitted:
                return "Could not submit prompt"
            
            # Wait for response
            logger.info("Waiting for Copilot response...")
            time.sleep(20)  # Increased wait time
            
            # Wait for response to appear - look for loading indicators to disappear
            try:
                # Additional wait for streaming
                time.sleep(5)
            except:
                pass
            
            # Try to find response - Copilot uses various formats
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
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    for elem in reversed(elements):
                        answer = elem.text.strip()
                        if (answer and 
                            len(answer) > len(best_answer) and 
                            len(answer) > 50 and 
                            prompt[:50].lower() not in answer.lower()):
                            best_answer = answer
                            logger.info(f"Found answer ({len(answer)} chars) using: {selector}")
                except:
                    continue
            
            if best_answer:
                return best_answer
            
            # Fallback - get all bot messages
            try:
                # Try shadow DOM access for Copilot's web components
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
                    logger.info(f"Got answer via JavaScript ({len(answer)} chars)")
                    return answer
            except Exception as e:
                logger.debug(f"JavaScript extraction failed: {e}")
            
            # Last resort
            try:
                main = self.driver.find_element(By.CSS_SELECTOR, "main, #b_sydConvCont, cib-serp")
                answer = main.text.strip()
                if answer and len(answer) > 100:
                    return answer
            except:
                pass
                
        except Exception as e:
            logger.error(f"Copilot extraction error: {e}")
        
        return "Could not extract answer"
    
    def extract_gemini(self, prompt):
        """Extract response from Google Gemini"""
        try:
            # Wait for page load
            time.sleep(3)
            
            # Find input field
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
                        logger.info(f"Found Gemini input using: {selector}")
                        break
                except:
                    continue
            
            if not input_box:
                return "Could not find input box"
            
            # Send prompt
            input_box.click()
            time.sleep(1)
            
            # Clear for contenteditable
            try:
                input_box.clear()
            except:
                input_box.send_keys(Keys.COMMAND + "a")
                input_box.send_keys(Keys.DELETE)
                time.sleep(0.5)
            
            input_box.send_keys(prompt)
            time.sleep(1)
            
            # Submit - Gemini uses a send button
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
                        logger.info(f"Clicked send button: {selector}")
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
            
            # Wait for response
            logger.info("Waiting for Gemini response...")
            time.sleep(12)
            
            # Additional wait if streaming
            time.sleep(3)
            
            # Try to find response
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
                        if (answer and 
                            len(answer) > len(best_answer) and 
                            len(answer) > 50 and 
                            prompt[:50].lower() not in answer.lower()):
                            best_answer = answer
                            logger.info(f"Found answer ({len(answer)} chars) using: {selector}")
                except:
                    continue
            
            if best_answer:
                return best_answer
            
            # Fallback
            try:
                main = self.driver.find_element(By.TAG_NAME, "main")
                answer = main.text.strip()
                if answer and len(answer) > 100:
                    # Try to filter out the prompt
                    if prompt[:50] in answer[:300]:
                        parts = answer.split(prompt[:50], 1)
                        if len(parts) > 1:
                            answer = parts[1].strip()
                    if answer and len(answer) > 100:
                        return answer
            except:
                pass
                
        except Exception as e:
            logger.error(f"Gemini extraction error: {e}")
        
        return "Could not extract answer"
    
    def extract_response(self, llm, prompt, prompt_index, retry_count=0, max_retries=2):
        """Extract response from a specific LLM with retry logic"""
        logger.info(f"[{prompt_index + 1}/{len(self.prompts)}] Processing on {llm}")
        
        try:
            self.driver.get(self.llms[llm])
            time.sleep(3)
            
            # Extract based on LLM
            if llm == "Perplexity":
                answer = self.extract_perplexity(prompt)
            elif llm == "ChatGPT":
                answer = self.extract_chatgpt(prompt)
            elif llm == "Claude":
                answer = self.extract_claude(prompt)
            elif llm == "Grok":
                answer = self.extract_grok(prompt)
            elif llm == "Copilot":
                answer = self.extract_copilot(prompt)
            elif llm == "Gemini":
                answer = self.extract_gemini(prompt)
            else:
                answer = "Unknown LLM"
            
            # Determine status
            if answer and "Login required" in answer:
                status = "login_required"
            elif (answer and 
                  answer != "Could not extract answer" and 
                  answer != "Could not send prompt" and
                  answer != "Could not find input box"):
                status = "success"
            else:
                status = "failed"
            
            # Retry if failed and retries available (but not for login required)
            if status == "failed" and retry_count < max_retries:
                logger.warning(f"Extraction failed for {llm}, retrying... ({retry_count + 1}/{max_retries})")
                time.sleep(5)
                return self.extract_response(llm, prompt, prompt_index, retry_count + 1, max_retries)
            elif status == "login_required":
                logger.warning(f"{llm} requires login - skipping retries")
            
            logger.info(f"Extracted {len(answer) if answer else 0} chars - Status: {status}")
            
            # Summarize the answer if extraction was successful
            summarized_answer = answer
            if status == "success" and answer and len(answer) > 100:
                logger.info(f"Summarizing answer from {llm}...")
                summarized_answer = self.summarize_text(answer)
            
            self.results.append({
                "llm": llm, 
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "full_prompt": prompt,
                "original_answer": answer,
                "summarized_answer": summarized_answer,
                "answer_length": len(answer) if answer else 0,
                "summary_length": len(summarized_answer) if summarized_answer else 0,
                "status": status,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
        except TimeoutException as e:
            logger.error(f"Timeout on {llm}: {str(e)}")
            self.results.append({
                "llm": llm, 
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "full_prompt": prompt,
                "answer": None,
                "answer_length": 0,
                "status": "timeout",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
        except Exception as e:
            logger.error(f"Error on {llm}: {str(e)}")
            self.results.append({
                "llm": llm, 
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "full_prompt": prompt,
                "answer": None,
                "answer_length": 0,
                "status": f"error",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    def save_progress(self):
        """Save current results to CSV"""
        if self.results:
            df = pd.DataFrame(self.results)
            df.to_csv(self.output_csv, index=False)
            logger.info(f"Progress saved to {self.output_csv}")
    
    def run(self, llm_subset=None, prompt_limit=None):
        """
        Main execution method
        
        Args:
            llm_subset: List of LLM names to process (None = all)
            prompt_limit: Max number of prompts to process (None = all)
        """
        try:
            self.setup_driver()
            
            llms_to_process = llm_subset if llm_subset else list(self.llms.keys())
            prompts_to_process = self.prompts[:prompt_limit] if prompt_limit else self.prompts
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting extraction")
            logger.info(f"LLMs: {', '.join(llms_to_process)}")
            logger.info(f"Prompts: {len(prompts_to_process)}")
            logger.info(f"{'='*60}\n")
            
            for llm in llms_to_process:
                logger.info(f"\n{'='*60}")
                logger.info(f"Processing LLM: {llm}")
                logger.info(f"{'='*60}\n")
                
                for idx, prompt in enumerate(prompts_to_process):
                    self.extract_response(llm, prompt, idx)
                    
                    # Save progress every 5 prompts
                    if (idx + 1) % 5 == 0:
                        self.save_progress()
                    
                    # Delay between prompts
                    if idx < len(prompts_to_process) - 1:
                        time.sleep(5)
                
                # Delay between LLMs
                if llm != llms_to_process[-1]:
                    logger.info(f"\nCompleted {llm}. Waiting 15 seconds before next LLM...\n")
                    time.sleep(15)
        
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed")
            
            # Final save
            self.save_progress()
            
            # Print summary
            self.print_summary()
    
    def print_summary(self):
        """Print extraction summary"""
        if not self.results:
            logger.warning("No results to summarize")
            return
        
        df = pd.DataFrame(self.results)
        
        logger.info("\n" + "="*60)
        logger.info("EXTRACTION SUMMARY")
        logger.info("="*60)
        logger.info(f"Total responses attempted: {len(self.results)}")
        logger.info(f"Successful: {len(df[df['status'] == 'success'])}")
        logger.info(f"Failed: {len(df[df['status'] == 'failed'])}")
        logger.info(f"Login Required: {len(df[df['status'] == 'login_required'])}")
        logger.info(f"Timeout: {len(df[df['status'] == 'timeout'])}")
        logger.info(f"Errors: {len(df[df['status'] == 'error'])}")
        logger.info(f"\nBreakdown by LLM:")
        for llm in df['llm'].unique():
            llm_df = df[df['llm'] == llm]
            success_rate = len(llm_df[llm_df['status'] == 'success']) / len(llm_df) * 100
            logger.info(f"  {llm}: {success_rate:.1f}% success rate")
        logger.info(f"\nResults saved to: {self.output_csv}")
        logger.info("="*60)


if __name__ == "__main__":
    # Run extraction on first 5 prompts for each LLM
    agent = AIExtractionAgent()
    agent.run(prompt_limit=5)

    