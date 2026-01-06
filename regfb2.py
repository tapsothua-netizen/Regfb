#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import random
import re
import datetime
import platform
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pystyle import Colors, Colorate
from logging import getLogger, StreamHandler, ERROR

# ================= CẤU HÌNH =================
HOME = os.path.expanduser("~")
DESKTOP = os.path.join(HOME, "Desktop")
IS_WINDOWS = platform.system().lower().startswith("win")

# Tên file lưu kết quả
OUTPUT_FILE = os.path.join(DESKTOP, "PhuocAn_RegFB_Final_OkButton.txt")
SCREENSHOT_DIR = os.path.join(DESKTOP, "Reg_Screenshots")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["WDM_LOG_LEVEL"] = "0"

# ================= LOGGER =================
logger = getLogger("reg_bot")
logger.setLevel(ERROR)
if logger.hasHandlers(): logger.handlers.clear()
ch = StreamHandler()
ch.setLevel(ERROR)
logger.addHandler(ch)

def debug(msg, level=1):
    if level >= 1: 
        prefix = {1: "ℹ️", 2: "⚙️", 3: "🌀", 4: "📡", 5: "🔥"}.get(level, "ℹ️")
        print(Colorate.Horizontal(Colors.cyan_to_blue, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {prefix} {msg}"))

# ================= DATA =================
def random_vn_name():
    first = ["Nguyễn","Trần","Lê","Phạm","Hoàng","Huỳnh","Phan","Vũ","Đặng","Bùi"]
    mid = ["Văn","Thị","Đức","Thành","Minh","Quốc","Công","Hữu","Trọng","Tấn"]
    last = ["An","Bình","Cường","Dũng","Hùng","Kiệt","Long","Nam","Linh","Quý"]
    return f"{random.choice(first)} {random.choice(mid)} {random.choice(last)}"

def random_birthday():
    year = random.randint(1996, 2002)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return str(day), str(month), str(year)

def random_password(length=12):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#"
    return "Minh@" + ''.join(random.choice(chars) for _ in range(length))

# ================= HUMAN TYPING =================
def human_type(element, text):
    """Gõ phím như người thật"""
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2)) 

# ================= DRIVER SETUP =================
def create_driver():
    opts = Options()
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-notifications")
    
    # Random size
    w = random.randint(1000, 1200)
    h = random.randint(800, 1000)
    opts.add_argument(f"--window-size={w},{h}")
    
    # Anti-detect
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    opts.add_experimental_option('useAutomationExtension', False)
    
    # Fake UA
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    opts.add_argument(f"user-agent={ua}")
    opts.add_argument("--log-level=3")

    service = Service(ChromeDriverManager().install(), log_output=subprocess.DEVNULL)
    driver = webdriver.Chrome(service=service, options=opts)
    
    # Bypass navigator.webdriver
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

# ================= TAB HANDLING =================
def prepare_tabs(driver):
    driver.get("https://www.facebook.com/reg")
    driver.execute_script("window.open('https://emailsll.net/mailbox', '_blank');")
    
    driver.switch_to.window(driver.window_handles[1])
    debug("Đang lấy email...", 2)
    time.sleep(6) 
    
    email = None
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', body_text)
        valid_emails = [e for e in emails if "contact" not in e and "support" not in e and "domain" not in e]
        if valid_emails:
            email = valid_emails[0]
        else:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                val = inp.get_attribute("value")
                if val and "@" in val:
                    email = val
                    break
    except: pass
    
    driver.switch_to.window(driver.window_handles[0])
    return email

def check_code_tab(driver, timeout=120):
    debug(f"Chuyển Tab Mail tìm code...", 2)
    driver.switch_to.window(driver.window_handles[1])
    
    start_time = time.time()
    code = None
    driver.refresh()
    time.sleep(3)

    while time.time() - start_time < timeout:
        try:
            elapsed = int(time.time() - start_time)
            # Refresh mỗi 15s
            if elapsed > 0 and elapsed % 15 == 0:
                debug(f"🔄 Refresh mail (giây {elapsed})...", 1)
                driver.refresh()
                time.sleep(4)

            body_text = driver.find_element(By.TAG_NAME, "body").text
            
            codes = re.findall(r'FB-(\d{5})', body_text)
            if not codes:
                codes = re.findall(r'\b\d{5}\b', body_text)
            
            if codes:
                code = codes[0]
                break
                
            if "Facebook" in body_text and not code:
                try:
                    elems = driver.find_elements(By.XPATH, "//*[contains(text(), 'Facebook')]")
                    for el in elems:
                        if el.is_displayed():
                            el.click()
                            break
                except: pass
        except: pass
        time.sleep(1)
            
    driver.switch_to.window(driver.window_handles[0])
    return code

# ================= REG FLOW =================
def register_account(index):
    fullname = random_vn_name()
    p = fullname.split()
    first, last = p[-1], " ".join(p[:-1])
    day, month, year = random_birthday()
    
    driver = None
    try:
        driver = create_driver()
        
        # 1. LẤY MAIL
        email = prepare_tabs(driver)
        if not email:
            print(Colorate.Horizontal(Colors.red_to_white, f"[{index}] ❌ Lỗi Mail (Skip)"))
            return

        fb_pass = random_password(12)
        print(Colorate.Horizontal(Colors.yellow_to_red, f"\n[{index}] Reg: {fullname} | {email}"))
        
        # 2. ĐIỀN FORM
        wait = WebDriverWait(driver, 20)
        
        elem_first = wait.until(EC.presence_of_element_located((By.NAME, "firstname")))
        human_type(elem_first, first)
        
        elem_last = driver.find_element(By.NAME, "lastname")
        human_type(elem_last, last)
        
        elem_email = driver.find_element(By.NAME, "reg_email__")
        human_type(elem_email, email)
        
        time.sleep(1)
        try:
            confirm = driver.find_element(By.NAME, "reg_email_confirmation__")
            if confirm.is_displayed(): 
                human_type(confirm, email)
        except: pass
        
        elem_pass = driver.find_element(By.NAME, "reg_passwd__")
        human_type(elem_pass, fb_pass)
        
        Select(driver.find_element(By.NAME, "birthday_day")).select_by_value(day)
        Select(driver.find_element(By.NAME, "birthday_month")).select_by_value(month)
        Select(driver.find_element(By.NAME, "birthday_year")).select_by_value(year)
        
        try: 
            driver.find_elements(By.NAME, "sex")[0].click()
            time.sleep(1)
        except: pass

        # 3. SUBMIT
        debug("Bấm đăng ký...", 1)
        time.sleep(1)
        
        try: driver.find_element(By.NAME, "websubmit").click()
        except: driver.execute_script("document.querySelector('button[name=websubmit]').click()")
            
        debug("Đã Submit, đợi phản hồi...", 2)
        time.sleep(10)
        
        if "checkpoint" in driver.current_url:
             print(Colorate.Horizontal(Colors.red_to_white, f"[{index}] ❌ Checkpoint ngay sau Submit!"))
             return 
        
        # 4. TÌM & NHẬP CODE
        code = check_code_tab(driver, timeout=120)
        
        if code:
            print(Colorate.Horizontal(Colors.green_to_white, f"[{index}] ✅ Đã có Code: {code}"))
            
            try:
                debug("Đang nhập code xác minh...", 2)
                # Tìm ô nhập code
                inp_code = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "code"))
                )
                human_type(inp_code, code)
                time.sleep(1)
                
                # Bấm xác nhận
                try:
                    driver.find_element(By.NAME, "confirm").click()
                except:
                    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
                
                debug("Đã nhập, đợi popup 'Đã xác nhận'...", 2)
                
                # --- NEW: XỬ LÝ POPUP "Ok" ---
                try:
                    # Tìm nút Ok theo hình ảnh bạn cung cấp
                    # Ưu tiên tìm đúng chữ "Ok"
                    ok_xpath = "//button[text()='Ok'] | //a[text()='Ok'] | //span[text()='Ok'] | //div[text()='Ok']"
                    ok_xpath += " | //button[contains(text(),'Ok')] | //a[contains(text(),'Ok')]"

                    # Chờ nút Ok xuất hiện (Max 15s)
                    ok_btn = WebDriverWait(driver, 15).until(
                        EC.element_to_be_clickable((By.XPATH, ok_xpath))
                    )
                    
                    debug("✨ Đã thấy popup 'Đã xác nhận tài khoản'!", 3)
                    time.sleep(1)
                    ok_btn.click()
                    debug("✅ Đã bấm nút 'Ok'!", 2)
                    
                except Exception:
                    debug("Không thấy nút Ok (Có thể FB tự chuyển hướng)", 2)
                # -----------------------------

                # --- ĐỢI TRANG CHỦ ---
                debug("Đang đợi vào Trang chủ...", 2)
                try:
                    # Điều kiện thành công: URL không còn chứa 'confirmemail' hay 'reg'
                    WebDriverWait(driver, 20).until(
                        lambda d: "confirmemail" not in d.current_url and "reg" not in d.current_url
                    )
                    
                    time.sleep(5)
                    
                    if "checkpoint" in driver.current_url:
                         print(Colorate.Horizontal(Colors.red_to_white, f"[{index}] ❌ Đã xác minh nhưng bị Checkpoint Login!"))
                         # Vẫn lưu nhưng đánh dấu CP
                         with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                            f.write(f"{email}|{fb_pass}|{fullname}|{day}/{month}/{year}|{code}|CP_LOGIN\n")
                    else:
                         print(Colorate.Horizontal(Colors.green_to_white, f"[{index}] 🎉 DONE! ĐÃ VÀO TRANG CHỦ!"))
                         with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                            f.write(f"{email}|{fb_pass}|{fullname}|{day}/{month}/{year}|{code}|LIVE\n")
                            
                except Exception:
                    print(Colorate.Horizontal(Colors.red_to_white, f"[{index}] ❌ Lỗi: Treo ở màn hình xác minh."))
            
            except Exception as e:
                debug(f"Lỗi nhập code: {e}", 4)

        else:
            print(Colorate.Horizontal(Colors.red_to_white, f"[{index}] ❌ Timeout (Không nhận được code)"))

    except Exception as e:
        debug(f"Lỗi acc {index}: {str(e)}", 4)
    finally:
        if driver:
            try: driver.quit()
            except: pass

# ================= RUN =================
def main():
    if IS_WINDOWS: os.system("cls")
    else: os.system("clear")
    print(Colorate.Horizontal(Colors.rainbow, "TOOL REG FB - AUTO OK POPUP"))
    try: n = int(input("Số lượng: "))
    except: n = 1
    for i in range(1, n + 1):
        register_account(i)
        if i < n: 
            print("Nghỉ 10s đổi IP...")
            time.sleep(10)
    print(Colorate.Horizontal(Colors.green_to_white, f"\nFile lưu tại: {OUTPUT_FILE}"))

if __name__ == "__main__":
    main()
