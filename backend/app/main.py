from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from crawler import AnimeScraper
from selenium import webdriver
import uuid
import os
import time
import requests
from pathlib import Path
from pydantic import BaseModel

app = FastAPI()
crawler = AnimeScraper()

# 存放下載進度
download_tasks = {}

class ParseRequest(BaseModel):
    url: str

@app.post("/api/parse")
def parse_anime(payload: ParseRequest):
    try:
        result = crawler.parse_anime_page(payload.url)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{task_id}")
def get_progress(task_id: str):
    task = download_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

class EpisodeItem(BaseModel):
    name: str
    link: str
    cookies: dict 

class DownloadRequest(BaseModel):
    episodes: list[EpisodeItem] 
    base_path: str
    anime_title: str

# 2. 徹底解放！完全不需要 Selenium 的純 requests 超輕量下載器
def async_download_worker(task_id: str, episodes: list[EpisodeItem], dest_path: str):
    download_tasks[task_id] = {
        "status": "downloading",
        "progress": 0,
        "current_file": episodes[0].name if episodes else ""
    }
    
    total_files = len(episodes)
    if total_files == 0:
        download_tasks[task_id]["status"] = "completed"
        download_tasks[task_id]["progress"] = 100
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Accept": "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
    }

    os.makedirs(dest_path, exist_ok=True)

    for index, epi in enumerate(episodes):
        download_tasks[task_id]["current_file"] = epi.name
        file_full_path = os.path.join(dest_path, f"{epi.name}.mp4")
        
        try:
            parts = epi.link.split('/')
            headers["Referer"] = f"https://anime1.me/{parts[-2]}/"
            
            with requests.get(epi.link, headers=headers, cookies=epi.cookies, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                dl_size = 0
                with open(file_full_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=10240):
                        if chunk:
                            f.write(chunk)
                            dl_size += len(chunk)
                            if total_size > 0:
                                file_progress = (dl_size / total_size) * 100
                                total_progress = (index / total_files) * 100 + (file_progress / total_files)
                                download_tasks[task_id]["progress"] = round(total_progress, 2)
                                
        except Exception as e:
            print(f"下載 {epi.name} 失敗: {e}")
        
        time.sleep(2)

    download_tasks[task_id]["progress"] = 100
    download_tasks[task_id]["status"] = "completed"


@app.post("/api/download")
def start_download(payload: DownloadRequest, background_tasks: BackgroundTasks):
    cleaned_path = payload.base_path.strip()
    if not cleaned_path:
        raise HTTPException(status_code=400, detail="下載請求拒絕：未偵測到有效的儲存路徑。")
        
    dest_path = os.path.join(cleaned_path, payload.anime_title.strip())
    task_id = str(uuid.uuid4())
    
    download_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "current_file": ""
    }
    
    background_tasks.add_task(
        async_download_worker, 
        task_id, 
        payload.episodes, 
        dest_path
    )
    
    return {"status": "success", "task_id": task_id}