import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import requests
import os
import copy
from tqdm import tqdm 
from pathlib import Path

driver = None

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Accept": "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}

def get_driver(url):
    global driver
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        driver.get(url)
    except:
        print("Can't get this url")
    return

def push_the_button():
   try:
        time.sleep(3)
        play_buttons = driver.find_elements(By.CSS_SELECTOR, 'button.vjs-big-play-button')
        print(f"找到 {len(play_buttons)} 個播放按鈕。")
        downloaded_src = []
        titles = []
        for i, button in enumerate(play_buttons):
            print(f"正在點擊第 {i+1} 個按鈕...")
            try:
                driver.execute_script("arguments[0].click();", button)
                print(f"已點擊第 {i+1} 個按鈕")
                time.sleep(2)
                all_videos = driver.find_elements(By.TAG_NAME, 'video')
                
                if (i + 1) == len(play_buttons):
                    titles = get_all_titles()
                    downloaded_src = get_all_link(all_videos)
                
            except Exception as e:
                print(f"點擊或處理第 {i+1} 個按鈕時發生錯誤: {e}")
                downloaded_src.append(None)
        """      
        if downloaded_src:
            for i in downloaded_src:
               print(i)
        if titles:
            for i in titles:
                print(i)
        """
   except:
       print("something wrong")
   
   return titles, downloaded_src

def get_all_link(all_videos):
    download_links = []
    for video_element in all_videos:
        src_link = video_element.get_attribute('src')
        download_links.append(src_link)
    return download_links

def get_all_titles():
    titles = []
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'h2.entry-title'))
        )
        all_titles = driver.find_elements(By.CSS_SELECTOR, 'h2.entry-title')
        for elements in all_titles:
            name = elements.text
            name = name.replace(" [", "").replace("]", "")
            #print(name)
            titles.append(name)
    except TimeoutException:
        print("在5秒內未檢測到 <h2 class='entry-title'> 元素")
    except Exception as e:
        print(f"獲取 entry titles 時發生錯誤: {e}")
    return titles

def check_titles(all_titles):
    for i in range(len(all_titles)):
        if all_titles[i].find(':') != -1:
            all_titles[i] = all_titles[i].replace(':', '')
    return

def make_file_directory(directory_name):
    try:
        path = Path.home() / "Desktop" / directory_name
        path.mkdir(parents=True, exist_ok=True)
        
        print(f"資料夾 '{directory_name}' 已成功創建在桌面")
        return str(path)
    except Exception as e:
        print(f"創建資料夾時發生錯誤: {e}")
        return None

def download_mp4(links, name, path):
    episodes = len(name)
    for i in range(episodes):
        print(f"正在下載：{name[i]}")
        name[i] += '.mp4'
        tmp_header = copy.deepcopy(headers)
        #tmp_header["Referer"] = links[i]
        parts = links[i].split('/')
        tmp_header["Referer"] = f"https://anime1.me/{parts[-2]}/"
        #print(tmp_header["Referer"])
        Cookies = get_cookies(links[i])
        try:
            with requests.get(links[i], headers = tmp_header, cookies = Cookies, stream = True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                if total_size == 0:
                    print("Can't find any size information.")
                    with open(f"{path}/{name[i]}", 'wb') as f:
                        for chunck in r.iter_content(chunk_size=10240):
                            f.write(chunck)
                    print("檔案已成功下載並儲存\n")
                else:
                    custom_bar_format = '{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}]'
                    with tqdm(total = total_size, unit = 'B', unit_scale = True, 
                              desc = name[i], bar_format = custom_bar_format) as progress_bar:
                        with open(f"{path}/{name[i]}", 'wb') as f:
                            for chunk in r.iter_content(chunk_size=10240):
                                f.write(chunk)
                                progress_bar.update(len(chunk))
                        print("檔案已成功下載並儲存\n")
        except requests.exceptions.RequestException as e:
            print(f"下載失敗 (網路或請求錯誤): {e}")
        except IOError as e:
            print(f"檔案寫入失敗 (可能是路徑問題或權限不足): {e}")
        except Exception as e:
            print(f"發生未知錯誤: {e}")
        time.sleep(2)

def get_cookies(url):
    driver.get(url)
    selenium_cookies = driver.get_cookies()
    requests_cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
    print("已成功從 Selenium 會話中獲取 Cookie。")
    # 打印一些關鍵的 Cookie 資訊，用於除錯
    if 'p' in requests_cookies:
        print(f"成功發現關鍵 Cookie 'p': {requests_cookies['p'][:10]}...")
    else:
        print("waring：未發現關鍵 Cookie 'p'。下載可能仍會失敗。")
        print("獲取的 Cookie 列表為:", requests_cookies)
    return requests_cookies

def main():
    my_url = str(input("輸入動畫網址: "))
    my_download_src = []
    my_titles = []
    get_driver(my_url)
    my_titles, my_download_src = push_the_button()
    print()
    check_titles(my_titles)
    #cookies = get_cookies()
    #print(cookies)
    directory_name = my_titles[0][:-2]
    dir_path = make_file_directory(directory_name)
    if dir_path:
        print()
        download_mp4(my_download_src, my_titles, dir_path)
    else:
        print("路徑創建失敗，停止下載")
    print()
    # download_mp4(my_download_src, my_titles, dir_path)
    #print(directory_name)
    #print(my_download_src)
    #print(my_titles)
    time.sleep(10)
    driver.close()
    print("end.")
main()