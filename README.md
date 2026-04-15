# Anime1-Downloader
基於 Python 的 anime1 下載器

> [!CAUTION]
> **本專案僅供程式實作練習與技術交流使用，請勿用於非法下載或侵犯版權之行為**

## 功能特點
- **動態爬蟲**：利用 Selenium 處理 JavaScript 渲染，自動獲取播放組件
- **Session 轉移**：將 Selenium 的 Cookie 注入 Requests，繞過驗證機制進行下載
- **進度可視化**：整合 `tqdm` 模組，即時顯示下載進度條
- **自動化管理**：自動建立資料夾並過濾非法字元（如 `:`）

## 技術棧
- Python 3.x
- Selenium (WebDriver)
- Requests (Binary Streaming)

##  安裝套件
   ```bash
   pip install -r requirements.txt
   ```
## .exe使用
1. 請確保電腦防毒不會將其刪除，可自行關閉防毒，但後果自負
2. 因爬蟲所需，請確保電腦已安裝 `Chrome 瀏覽器`，且程式會自動偵測環境
3. 使用此方法者，不需要安裝套件
