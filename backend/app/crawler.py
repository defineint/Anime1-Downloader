import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AnimeScraper:
    def __init__(self):
        self.driver = None

    def get_driver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # 偵測到環境變數有獨立 Chrome URL，就走遠端驅動，否則走本機
        selenium_url = os.getenv("SELENIUM_URL", None)
        if selenium_url:
            self.driver = webdriver.Remote(command_executor=selenium_url, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)

    def parse_anime_page(self, url: str):
        self.get_driver()
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # 點擊所有播放按鈕以觸發驗證與載入
            play_buttons = self.driver.find_elements(By.CSS_SELECTOR, 'button.vjs-big-play-button')
            for button in play_buttons:
                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(1.5)
                
            # 撈取所有集數標題
            all_titles = self.driver.find_elements(By.CSS_SELECTOR, 'h2.entry-title')
            titles = [t.text.replace(" [", "").replace("]", "").replace(':', '') for t in all_titles]
            
            # 撈取所有影片來源連結
            all_videos = self.driver.find_elements(By.TAG_NAME, 'video')
            video_srcs = [v.get_attribute('src') for v in all_videos]
            
            episodes_data = []
            for t, src in zip(titles, video_srcs):
                if src:
                    self.driver.get(src)
                    selenium_cookies = self.driver.get_cookies()
                    cookies_dict = {c['name']: c['value'] for c in selenium_cookies}
                    
                    # 標題、連結、Cookie 打包
                    episodes_data.append({
                        "name": t,
                        "link": src,
                        "cookies": cookies_dict
                    })
            
            anime_title = titles[0][:-2] if titles else "Unknown"
            return {"title": anime_title, "episodes": episodes_data}
            
        finally:
            if self.driver:
                self.driver.quit()