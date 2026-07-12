# Anime1 Downloader

一個可以使用私有雲、Home Server 與 NAS 的內網動漫下載全端工具。採用無狀態前端與安全沙盒後端架構，支援 Docker Compose 一鍵部署。

---

## 專案特性

- **一鍵部署**：內建多階段構建 Nginx 前端、FastAPI 後端以及獨立 Chrome 爬蟲服務。
- **安全沙盒**：後端全面阻絕任意路徑寫入漏洞，強制儲存於隔離的環境變數目錄。
- **併發下載**：採用多執行緒（ThreadPoolExecutor）技術，預設最高 3 併發安全流控。
- **進度輪詢**：前端與後端狀態獨立解耦，網頁重新整理亦能同步當前下載進度。

---

## 前置要求

在開始部署前，請確保您的主機已安裝以下環境：

- **Docker** (26.0.0+)
- **Docker Compose** (2.25.0+)

---

## 快速開始 (Deployment)

您不需要下載完整的原始碼，只需要下載 Release 頁面中的 `docker-compose.yml` 與 `.env.example` 即可：

### 1. 準備設定檔

將下載的 `.env.example` 重新命名為 `.env`：

```bash
cp .env.example .env
```

### 2. 配置儲存路徑

使用文字編輯器打開 .env，修改 ANIME_DOWNLOAD_PATH 為您伺服器或本機上想存放動漫的實體路徑：

```bash
ANIME_DOWNLOAD_PATH=/您的實體硬碟路徑/Anime
```

### 3. 一鍵啟動服務

在該目錄下執行以下指令，Docker 將自動拉取並組合所有服務：

```bash
docker compose up -d
```

### 4. 開始使用

部署完成後，打開瀏覽器輸入以下網址即可進入主介面：
`http://localhost:5173` (若是遠端伺服器，請將 localhost 換成您的伺服器 IP)

## 專案架構

```Plaintext
├── frontend/          # Vite + React 靜態前端 
├── backend/           # FastAPI 後端核心控制台
├── .env.example       # 環境變數配置範本
└── docker-compose.yml # 服務編排規格書
```

## 免責聲明

本專案僅供學術研究、個人技術練習（React 框架、FastAPI 與 Docker 容器化技術實踐）使用。請勿將本工具用於任何商業用途。使用者下載之所有內容版權皆屬原網站與原權利人所有，請於下載後 24 小時內刪除。
