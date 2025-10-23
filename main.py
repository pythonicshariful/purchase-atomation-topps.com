from inspect import cleandoc
import os
import time,random
import json
from turtle import clear
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# === Project setup ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(BASE_DIR, "chrome_profile")  # persistent user data
URL = "https://www.topps.com/"

def create_driver():
    """Create Chrome driver using a persistent local profile"""
    os.makedirs(PROFILE_DIR, exist_ok=True)

    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    options.add_argument("--remote-debugging-port=9222")
    driver = uc.Chrome(options=options)
    return driver

def human_type(element, text, min_delay=0.05, max_delay=0.18, pause_after=0.02):
    """
    Types `text` into `element` one character at a time with random delays.
    - min_delay/max_delay: per-char delay range in seconds
    - pause_after: small pause after finishing
    """
    element.clear()
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(min_delay, max_delay))
    time.sleep(pause_after)

def contactFormFill(driver):
    try:
        # Load contact info from config.json
        config_path = os.path.join(BASE_DIR, "config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        contact_info = config["contact_info"]
        payment_info = config["payment_info"]
        wait = WebDriverWait(driver, 10)
        
        # First name - using ID TextField0
        firstName = wait.until(EC.presence_of_element_located((By.ID, "TextField0")))
        firstName.clear()
        firstName.send_keys(contact_info["firstName"])
        
        # Last name - using ID TextField1
        lastName = wait.until(EC.presence_of_element_located((By.ID, "TextField1")))
        lastName.clear()
        lastName.send_keys(contact_info["lastName"])
        
        # Address - using ID shipping-address1
        address = wait.until(EC.presence_of_element_located((By.ID, "shipping-address1")))
        address.clear()
        address.send_keys(contact_info["address"])
        
        # City - using ID TextField3
        city = wait.until(EC.presence_of_element_located((By.ID, "TextField3")))
        city.clear()
        city.send_keys(contact_info["city"])
        
        # Select state from dropdown - using ID Select1
        state_dropdown = wait.until(EC.presence_of_element_located((By.ID, "Select1")))
        from selenium.webdriver.support.ui import Select
        state_select = Select(state_dropdown)
        state_select.select_by_value(contact_info["state"])
        
        # ZIP code - using ID TextField4
        zipCode = wait.until(EC.presence_of_element_located((By.ID, "TextField4")))
        zipCode.clear()
        zipCode.send_keys(contact_info["zipCode"])
        
        # Phone - using ID TextField5
        phone = wait.until(EC.presence_of_element_located((By.ID, "TextField5")))
        phone.clear()
        phone.send_keys(contact_info["phone"])
        
        # Fill payment information
        # Scroll to payment section and wait
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(random.uniform(2, 4))
        
        # Fill payment fields
        fill_payment_info(driver, payment_info)
        
        time.sleep(random.uniform(2, 4))

    except Exception as e:
        print(f"Error in contactFormFill: {e}")
        pass

def find_payment_iframe(driver, wait, field_type):
    """Helper function to find payment iframes by field type"""
    iframe_selectors = [
        f"iframe[src*='{field_type}']",
        f"iframe[title*='{field_type.replace('_', ' ').title()}']",
        f"iframe[id*='{field_type}']",
        f"iframe.card-fields-iframe[src*='{field_type}']",
        f"iframe[class*='card-fields-iframe'][src*='{field_type}']"
    ]
    
    # Add specific selectors for each field type
    if field_type == "number":
        iframe_selectors.extend([
            "iframe[title*='Card number']",
            "iframe[src*='number-ltr.html']"
        ])
    elif field_type == "expiry":
        iframe_selectors.extend([
            "iframe[title*='Expiration date']",
            "iframe[src*='expiry-ltr.html']"
        ])
    elif field_type == "verification_value":
        iframe_selectors.extend([
            "iframe[title*='Security code']",
            "iframe[src*='verification_value-ltr.html']"
        ])
    elif field_type == "name":
        iframe_selectors.extend([
            "iframe[title*='Name on card']",
            "iframe[src*='name-ltr.html']"
        ])
    
    for selector in iframe_selectors:
        try:
            iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            return iframe
        except:
            continue
    return None

def fill_payment_info(driver, payment_info):
    """Fill payment information in the checkout form"""
    try:
        wait = WebDriverWait(driver, 15)
        
        # Scroll to payment section to ensure it's visible
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(random.uniform(2, 3))
        
        # Fill name on card field (now also in iframe)
        try:
            name_iframe = find_payment_iframe(driver, wait, "name")
            
            if name_iframe:
                driver.switch_to.frame(name_iframe)
                time.sleep(random.uniform(0.5, 1))
                
                # Try multiple approaches to fill the name on card
                try:
                    # Approach 1: Direct interaction
                    name_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#number")))
                    name_input.click()
                    time.sleep(random.uniform(0.3, 0.5))
                    name_input.clear()
                    human_type(name_input, payment_info["nameOnCard"])
                except:
                    # Approach 2: JavaScript execution
                    try:
                        driver.execute_script("""
                            var input = document.querySelector('input');
                            if (input) {
                                input.focus();
                                input.value = arguments[0];
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        """, payment_info["nameOnCard"])
                    except:
                        pass
                
                driver.switch_to.default_content()
                time.sleep(random.uniform(0.5, 1))
                print("✅ Name on card filled successfully")
            else:
                print("❌ Could not find name on card iframe")
        except Exception as e:
            print(f"❌ Error filling name on card: {e}")
            driver.switch_to.default_content()
        
        # Fill card number (in iframe) - using dynamic iframe finding
        try:
            card_number_iframe = find_payment_iframe(driver, wait, "number")
            
            if card_number_iframe:
                driver.switch_to.frame(card_number_iframe)
                time.sleep(random.uniform(0.5, 1))
                
                # Try multiple approaches to fill the card number
                try:
                    # Approach 1: Direct interaction
                    card_number_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#verification_value")))
                    card_number_input.click()
                    time.sleep(random.uniform(0.3, 0.5))
                    card_number_input.clear()
                    human_type(card_number_input, payment_info["cardNumber"])
                except:
                    # Approach 2: JavaScript execution
                    try:
                        driver.execute_script("""
                            var input = document.querySelector('input');
                            if (input) {
                                input.focus();
                                input.value = arguments[0];
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        """, payment_info["cardNumber"])
                    except:
                        pass
                
                driver.switch_to.default_content()
                time.sleep(random.uniform(0.5, 1))
                print("✅ Card number filled successfully")
            else:
                print("❌ Could not find card number iframe")
        except Exception as e:
            print(f"❌ Error filling card number: {e}")
            driver.switch_to.default_content()
        
        # Fill expiry date (in iframe) - using dynamic iframe finding
        try:
            expiry_iframe = find_payment_iframe(driver, wait, "expiry")
            
            if expiry_iframe:
                driver.switch_to.frame(expiry_iframe)
                time.sleep(random.uniform(0.5, 1))
                
                # Try multiple approaches to fill the expiry date
                try:
                    # Approach 1: Direct interaction
                    expiry_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#expiry")))
                    expiry_input.click()
                    time.sleep(random.uniform(0.3, 0.5))
                    expiry_input.clear()
                    human_type(expiry_input, payment_info["expiryDate"])
                except:
                    # Approach 2: JavaScript execution
                    try:
                        driver.execute_script("""
                            var input = document.querySelector('input');
                            if (input) {
                                input.focus();
                                input.value = arguments[0];
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        """, payment_info["expiryDate"])
                    except:
                        pass
                
                driver.switch_to.default_content()
                time.sleep(random.uniform(0.5, 1))
                print("✅ Expiry date filled successfully")
            else:
                print("❌ Could not find expiry iframe")
        except Exception as e:
            print(f"❌ Error filling expiry date: {e}")
            driver.switch_to.default_content()
        
        # Fill security code/CVV (in iframe) - using dynamic iframe finding
        try:
            cvv_iframe = find_payment_iframe(driver, wait, "verification_value")
            
            if cvv_iframe:
                driver.switch_to.frame(cvv_iframe)
                time.sleep(random.uniform(0.5, 1))
                
                # Try multiple approaches to fill the security code
                try:
                    # Approach 1: Direct interaction
                    cvv_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[placeholder="Security code"]')))
                    cvv_input.click()
                    time.sleep(random.uniform(0.3, 0.5))
                    cvv_input.clear()
                    human_type(cvv_input, payment_info["securityCode"])
                except:
                    # Approach 2: JavaScript execution
                    try:
                        driver.execute_script("""
                            var input = document.querySelector('input');
                            if (input) {
                                input.focus();
                                input.value = arguments[0];
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        """, payment_info["securityCode"])
                    except:
                        pass
                
                driver.switch_to.default_content()
                time.sleep(random.uniform(0.5, 1))
                print("✅ Security code filled successfully")
            else:
                print("❌ Could not find CVV iframe")
        except Exception as e:
            print(f"❌ Error filling security code: {e}")
            driver.switch_to.default_content()
        
        # Fill phone number in the "Remember me" section if present
        try:
            phone_field = wait.until(EC.element_to_be_clickable((By.ID, "TextField8")))
            phone_field.click()
            time.sleep(random.uniform(0.3, 0.5))
            phone_field.clear()
            human_type(phone_field, payment_info.get("phone", "1234567890"))
            time.sleep(random.uniform(0.5, 1))
            print("✅ Phone number filled successfully")
        except Exception as e:
            print(f"⚠️ Phone number field not found or error: {e}")
        
        print("🎉 Payment information filled successfully!")
        
    except Exception as e:
        print(f"❌ Error in fill_payment_info: {e}")
        driver.switch_to.default_content()




class ToppsBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Topps Bot Configuration")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # Variables
        self.product_url = tk.StringVar()
        self.quantity = tk.StringVar(value="1")
        self.driver = None
        self.is_running = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Topps Bot Configuration", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Product URL
        ttk.Label(main_frame, text="Product URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        url_entry = ttk.Entry(main_frame, textvariable=self.product_url, width=50)
        url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Quantity
        ttk.Label(main_frame, text="Quantity:").grid(row=2, column=0, sticky=tk.W, pady=5)
        quantity_entry = ttk.Entry(main_frame, textvariable=self.quantity, width=10)
        quantity_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Start button
        self.start_button = ttk.Button(button_frame, text="Start Bot", 
                                      command=self.start_bot, style="Accent.TButton")
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        self.stop_button = ttk.Button(button_frame, text="Stop Bot", 
                                     command=self.stop_bot, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Status text
        self.status_text = tk.Text(status_frame, height=10, width=60, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(status_frame, orient="vertical", command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=scrollbar.set)
        
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        status_frame.columnconfigure(0, weight=1)
        status_frame.rowconfigure(0, weight=1)
        
    def log_message(self, message):
        """Add message to status log"""
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_bot(self):
        """Start the bot in a separate thread"""
        if not self.product_url.get().strip():
            messagebox.showerror("Error", "Please enter a product URL")
            return
            
        if not self.quantity.get().strip():
            messagebox.showerror("Error", "Please enter a quantity")
            return
            
        try:
            int(self.quantity.get())
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a number")
            return
            
        self.is_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        
        # Start bot in separate thread
        bot_thread = threading.Thread(target=self.run_bot)
        bot_thread.daemon = True
        bot_thread.start()
        
    def stop_bot(self):
        """Stop the bot"""
        self.is_running = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.log_message("🛑 Bot stopped by user")
        
    def run_bot(self):
        """Main bot logic"""
        try:
            self.log_message("🚀 Starting Topps Bot...")
            
            # Create driver
            self.driver = create_driver()
            self.driver.get(URL)
            
            self.log_message("🌐 Browser opened. Please complete any captcha or login manually.")
            self.log_message("⏳ Waiting for manual setup...")
            
            # Wait for user to complete setup
            time.sleep(3)
            
            product_url = self.product_url.get().strip()
            quantity = self.quantity.get().strip()
            
            self.log_message(f"📦 Navigating to product: {product_url}")
            self.driver.get(product_url)
            time.sleep(random.randint(3, 5))
            
            while self.is_running:
                try:
                    # Wait for the quantity input to be present
                    wait = WebDriverWait(self.driver, 10)
                    quantity_input = wait.until(EC.presence_of_element_located((By.NAME, "quantity")))
                    
                    # Clear the current value and set new quantity
                    quantity_input.clear()
                    quantity_input.send_keys(quantity)
                    
                    self.log_message(f"✅ Successfully set quantity to: {quantity}")
                    
                    # Click the "Add to cart" button
                    add_to_cart_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="product-add-to-cart"]')
                    add_to_cart_button.click()
                    self.log_message("✅ Added to cart successfully!")
                    
                    time.sleep(random.randint(3, 5))
                    try:
                        checkout = self.driver.find_element(By.CSS_SELECTOR, 'a[href="/checkout/cart"]')
                        checkout_url = checkout.get_attribute('href')
                        self.driver.get(checkout_url)
                        self.log_message("✅ Checkout page loaded successfully!")
                        break
                    except:
                        self.log_message("❌ Error: Checkout button not found")
                        pass
                        
                except TimeoutException:
                    self.log_message("❌ Timeout: Could not find quantity input element")
                    time.sleep(2)
                except NoSuchElementException:
                    self.log_message("❌ Error: Quantity input or add to cart button not found")
                    time.sleep(2)
                except Exception as e:
                    self.log_message(f"❌ Error: {str(e)}")
                    time.sleep(2)
            
            # Proceed to checkout if cart was successfully added
            if self.is_running:
                try:
                    self.log_message("🛒 Proceeding to checkout...")
                    wait = WebDriverWait(self.driver, 10)
                    checkoutBtn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue to checkout')]")))
                    checkoutBtn.click()
                    self.log_message("✅ Checkout button clicked successfully!")
                    contactFormFill(self.driver)
                    
                                      
                    
                    time.sleep(random.randint(3, 5))
                    
                    self.log_message("💳 Looking for pay now button...")
                    wait = WebDriverWait(self.driver, 10)
                    payNowBtn = wait.until(EC.element_to_be_clickable((By.ID, "checkout-pay-button")))
                    payNowBtn.click()
                    self.log_message("✅ Pay now button clicked successfully!")
                    time.sleep(random.randint(3, 5))
                    
                except TimeoutException:
                    self.log_message("❌ Timeout: Could not find checkout or pay button")
                except NoSuchElementException:
                    self.log_message("❌ Error: Checkout or pay button not found")
                except Exception as e:
                    self.log_message(f"❌ Error during checkout: {str(e)}")
                    
        except Exception as e:
            self.log_message(f"❌ Fatal Error: {str(e)}")
        finally:
            self.is_running = False
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")
       
 
    def run(self):
        """Start the GUI"""
        self.root.mainloop()

def main():
    """Main function to start the GUI"""
    app = ToppsBotGUI()
    app.run()

if __name__ == "__main__":
    main()
