from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from crawler import AnimeScraper
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ThreadPoolExecutor
import uuid
import os
import time
import requests
import threading

app = FastAPI()

# 配置 CORS，讓本地開發運行的 React (Port 5173) 能順利存取 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

crawler = AnimeScraper()

# 全域狀態管理字典
download_tasks = {}
# 執行緒鎖，確保多執行緒在寫入 progress_map 時不會發生衝突
progress_lock = threading.Lock()


class ParseRequest(BaseModel):
    url: str
    base_path: str = ""


@app.post("/api/parse")
def parse_anime(payload: ParseRequest):
    try:
        # 呼叫爬蟲核心撈取動漫網頁資訊
        result = crawler.parse_anime_page(payload.url)
        
        base_path = payload.base_path.strip()
        anime_title = result.get("title", "").strip()
        
        # 如果前端有傳送儲存路徑，則主動去硬碟掃描是否已有正式的 .mp4 完工檔
        if base_path and anime_title:
            dest_path = os.path.join(base_path, anime_title)
            for epi in result.get("episodes", []):
                file_full_path = os.path.join(dest_path, f"{epi['name']}.mp4")
                # 嚴格認定：只認存在且非臨時檔的 .mp4
                epi["is_existed"] = os.path.exists(file_full_path)
        else:
            for epi in result.get("episodes", []):
                epi["is_existed"] = False
                
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 調整三：定義各集獨立的資料格式 ====================
class EpisodeItem(BaseModel):
    name: str
    link: str
    cookies: dict

class DownloadRequest(BaseModel):
    episodes: list[EpisodeItem]
    base_path: str
    anime_title: str


def download_single_episode(task_id: str, epi: EpisodeItem, dest_path: str, headers: dict):
    """單一集數的下載執行緒"""
    file_temp_path = os.path.join(dest_path, f"{epi.name}.mp4.part") 
    file_full_path = os.path.join(dest_path, f"{epi.name}.mp4")      
    
    try:
        parts = epi.link.split('/')
        local_headers = headers.copy()
        local_headers["Referer"] = f"https://anime1.me/{parts[-2]}/"
        
        with requests.get(epi.link, headers=local_headers, cookies=epi.cookies, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            
            dl_size = 0
            # 1. 優先寫入到 .part 暫存檔，確保不污染正式檔名
            with open(file_temp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=10240):
                    if chunk:
                        f.write(chunk)
                        dl_size += len(chunk)
                        if total_size > 0:
                            file_progress = (dl_size / total_size) * 100
                            with progress_lock:
                                download_tasks[task_id]["progress_map"][epi.name] = round(file_progress, 2)
            
            # 2. 確定完整下載完畢後，將臨時檔更名回正式的 .mp4
            if os.path.exists(file_temp_path):
                if os.path.exists(file_full_path):
                    os.remove(file_full_path) # 若有舊檔先移除
                os.rename(file_temp_path, file_full_path)
                
            with progress_lock:
                download_tasks[task_id]["progress_map"][epi.name] = 100.0
                
    except Exception as e:
        print(f"下載 {epi.name} 發生錯誤: {e}")
        # 下載失敗時，清理殘留的 .part 髒資料
        if os.path.exists(file_temp_path):
            try:
                os.remove(file_temp_path)
            except:
                pass
        # 失敗也強制將進度歸為 100，避免前端進度條卡死
        with progress_lock:
            download_tasks[task_id]["progress_map"][epi.name] = 100.0


def async_download_worker(task_id: str, episodes: list[EpisodeItem], dest_path: str):
    """總指揮官：負責初始化任務並分派多執行緒"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "Accept": "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
    }
    os.makedirs(dest_path, exist_ok=True)

    # 限制最高併發下載數量為 3，兼顧效能與安全性
    MAX_CONCURRENT_DOWNLOADS = 3
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS) as executor:
        for epi in episodes:
            executor.submit(download_single_episode, task_id, epi, dest_path, headers)
            time.sleep(0.5) # 稍微錯開各執行緒的啟動，避免瞬間併發過高

    # 當線程池全部收工，更新主狀態
    with progress_lock:
        download_tasks[task_id]["status"] = "completed"


@app.post("/api/download")
def start_download(payload: DownloadRequest, background_tasks: BackgroundTasks):
    cleaned_path = payload.base_path.strip()
    if not cleaned_path:
        raise HTTPException(status_code=400, detail="下載請求拒絕：未偵測到有效的儲存路徑。")
        
    dest_path = os.path.join(cleaned_path, payload.anime_title.strip())
    task_id = str(uuid.uuid4())
    
    download_tasks[task_id] = {
        "status": "downloading",
        "anime_title": payload.anime_title.strip(),
        "progress_map": {epi.name: 0.0 for epi in payload.episodes}
    }
    
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