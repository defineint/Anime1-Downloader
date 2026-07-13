from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from crawler import AnimeScraper
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
import uuid
import os
import time
import json
import requests
import threading
import shutil

# 全域狀態與路徑配置
download_tasks = {}
progress_lock = threading.Lock()
DOWNLOAD_ROOT = os.getenv("DOWNLOAD_ROOT", "./downloads")
DB_FILE_PATH = os.path.join(DOWNLOAD_ROOT, "tasks_db.json")

# 容器內部原生的高速暫存目錄，徹底與外部掛載硬碟隔離
CONTAINER_TMP_DIR = "/tmp/anime_downloads"
os.makedirs(CONTAINER_TMP_DIR, exist_ok=True)

parse_cache = {}
crawler = AnimeScraper()

def save_tasks_to_db():
    try:
        with progress_lock:
            json_string = json.dumps(download_tasks, ensure_ascii=False, indent=4)
        with open(DB_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(json_string)
    except Exception as e:
        print(f"儲存任務紀錄失敗: {e}", flush=True)

def load_tasks_from_db():
    global download_tasks
    if os.path.exists(DB_FILE_PATH):
        try:
            with open(DB_FILE_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                for task_id, task in loaded.items():
                    if task["status"] in ["downloading", "pending"]:
                        task["status"] = "failed"
                download_tasks = loaded
                print(f"成功從硬碟載入 {len(download_tasks)} 筆歷史任務！")
        except Exception as e:
            print(f"載入歷史任務失敗: {e}", flush=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_tasks_from_db()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ParseRequest(BaseModel):
    url: str

@app.post("/api/parse")
def parse_anime(payload: ParseRequest):
    current_time = time.time()
    url_key = payload.url.strip()
    
    if url_key in parse_cache:
        cache_entry = parse_cache[url_key]
        if current_time - cache_entry["time"] < 600:
            print("[Cache Hit] 命中後端快取！全面攔截 Selenium，保護下載執行緒！", flush=True)
            result = cache_entry["data"]
            
            anime_title = result.get("title", "").strip()
            if anime_title:
                dest_path = os.path.join(DOWNLOAD_ROOT, anime_title)
                for epi in result.get("episodes", []):
                    file_full_path = os.path.join(dest_path, f"{epi['name']}.mp4")
                    epi["is_existed"] = os.path.exists(file_full_path)
            
            return {"status": "success", "data": result}

    try:
        print("[Cache Miss] 第一次解析或快取過期，啟動無頭 Chrome 側車...", flush=True)
        result = crawler.parse_anime_page(url_key)
        
        parse_cache[url_key] = {
            "time": current_time,
            "data": result
        }
        
        anime_title = result.get("title", "").strip()
        if anime_title:
            dest_path = os.path.join(DOWNLOAD_ROOT, anime_title)
            for epi in result.get("episodes", []):
                file_full_path = os.path.join(dest_path, f"{epi['name']}.mp4")
                epi["is_existed"] = os.path.exists(file_full_path)
        else:
            for epi in result.get("episodes", []):
                epi["is_existed"] = False
                
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class EpisodeItem(BaseModel):
    name: str
    link: str
    cookies: dict
    ua: str


class DownloadRequest(BaseModel):
    episodes: list[EpisodeItem]
    anime_title: str


def download_single_episode(task_id: str, epi: EpisodeItem, dest_path: str):
    local_temp_path = os.path.join(CONTAINER_TMP_DIR, f"{task_id}_{epi.name}.mp4.part")
    local_ready_path = os.path.join(CONTAINER_TMP_DIR, f"{task_id}_{epi.name}.mp4")
    
    # 使用者最終在 Windows 掛載硬碟看到的實體路徑
    final_destination_path = os.path.join(dest_path, f"{epi.name}.mp4")      
    
    try:
        parts = epi.link.split('/')
        local_headers = {
            "User-Agent": epi.ua,
            "Accept": "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Referer": f"https://anime1.me/{parts[-2]}/"
        }
        
        with requests.get(epi.link, headers=local_headers, cookies=epi.cookies, stream=True, timeout=15) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            dl_size = 0
            with open(local_temp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=262144):
                    if chunk:
                        f.write(chunk)
                        dl_size += len(chunk)
                        if total_size > 0:
                            file_progress = (dl_size / total_size) * 100
                            with progress_lock:
                                download_tasks[task_id]["progress_map"][epi.name] = round(file_progress, 2)
            
            # 在容器本地極速完成命名切換
            if os.path.exists(local_temp_path):
                if os.path.exists(local_ready_path):
                    os.remove(local_ready_path)
                os.rename(local_temp_path, local_ready_path)
                
                if os.path.exists(final_destination_path):
                    os.remove(final_destination_path)
                shutil.move(local_ready_path, final_destination_path)
                
            with progress_lock:
                download_tasks[task_id]["progress_map"][epi.name] = 100.0
            
            save_tasks_to_db()
                
    except Exception as e:
        print(f"[下載核心報報錯] {epi.name} 發生錯誤: {e}", flush=True)
        # 清理容器內殘留
        for p in [local_temp_path, local_ready_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass
        save_tasks_to_db()


def async_download_worker(task_id: str, episodes: list[EpisodeItem], dest_path: str):
    # 建立掛載硬碟的目標目錄
    os.makedirs(dest_path, exist_ok=True)

    MAX_CONCURRENT_DOWNLOADS = 3
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS) as executor:
        for epi in episodes:
            executor.submit(download_single_episode, task_id, epi, dest_path)
            time.sleep(0.5)

    with progress_lock:
        download_tasks[task_id]["status"] = "completed"
        
    save_tasks_to_db()


@app.post("/api/download")
def start_download(payload: DownloadRequest, background_tasks: BackgroundTasks):
    dest_path = os.path.join(DOWNLOAD_ROOT, payload.anime_title.strip())
    task_id = str(uuid.uuid4())
    
    download_tasks[task_id] = {
        "status": "downloading",
        "anime_title": payload.anime_title.strip(),
        "progress_map": {epi.name: 0.0 for epi in payload.episodes}
    }
    save_tasks_to_db()
    
    background_tasks.add_task(async_download_worker, task_id, payload.episodes, dest_path)
    return {"status": "success", "task_id": task_id}


@app.get("/api/progress/{task_id}")
def get_progress(task_id: str):
    task = download_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/active-tasks")
def get_active_tasks():
    active = {
        task_id: task for task_id, task in download_tasks.items()
        if task["status"] == "downloading"
    }
    return {"status": "success", "active_tasks": active}