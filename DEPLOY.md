# 財務稅法QA機器人 - 雲端部署指南

本文檔提供了將財務稅法QA機器人部署到各種雲端平台的詳細步驟。

## 目錄
- [Streamlit Cloud 部署](#streamlit-cloud-部署)
- [Render 部署](#render-部署)
- [Railway 部署](#railway-部署)
- [Heroku 部署](#heroku-部署)
- [常見問題](#常見問題)

## Streamlit Cloud 部署

Streamlit Cloud 是部署 Streamlit 應用最簡單的方式，完全免費且專為 Streamlit 應用設計。

### 前置準備

1. 確保您有一個 GitHub 帳戶
2. 確保您的專案已經推送到 GitHub 倉庫

### 部署步驟

1. 在 GitHub 上創建一個新的倉庫
   - 前往 [GitHub](https://github.com) 並登入
   - 點擊右上角的 "+" 圖標，選擇 "New repository"
   - 填寫倉庫名稱（例如：finance-tax-chatbot）
   - 選擇公開或私有（Streamlit Cloud 支持兩者）
   - 點擊 "Create repository"

2. 將本地倉庫推送到 GitHub：
   ```bash
   git remote add origin https://github.com/你的用戶名/你的倉庫名.git
   git push -u origin main
   ```

3. 前往 [Streamlit Cloud](https://streamlit.io/cloud) 並登入
   - 如果您沒有帳戶，可以使用 GitHub 帳戶註冊

4. 點擊 "New app" 按鈕

5. 在部署表單中填寫以下信息：
   - Repository: 選擇您的 GitHub 倉庫
   - Branch: main
   - Main file path: streamlit_app.py
   - App URL: 自動生成或自定義

6. 展開 "Advanced settings"，添加以下密鑰：
   - OPENAI_API_KEY: 您的 OpenAI API 密鑰（必需）
   - 其他可選的環境變數（如果需要）

7. 點擊 "Deploy" 按鈕

8. 等待部署完成，您的應用將在幾分鐘內上線
   - 您可以通過提供的 URL 訪問您的應用
   - 每次推送到 GitHub 倉庫時，應用會自動更新

### 注意事項

- Streamlit Cloud 免費版有一些限制，如應用數量和計算資源
- 確保您的 `.gitignore` 文件包含 `.env` 和其他敏感文件
- 不要將 API 密鑰提交到 GitHub 倉庫

## Render 部署

Render 是一個簡單易用的雲端平台，提供免費層級。

### 前置準備

1. 確保您有一個 [Render](https://render.com) 帳戶
2. 確保您的專案已經推送到 GitHub 倉庫

### 部署步驟

1. 在專案根目錄創建一個 `render.yaml` 文件：

```yaml
services:
  - type: web
    name: finance-tax-chatbot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: OPENAI_API_KEY
        sync: false
```

2. 將此文件提交並推送到 GitHub：
```bash
git add render.yaml
git commit -m "添加 Render 配置文件"
git push
```

3. 登入 [Render Dashboard](https://dashboard.render.com)

4. 點擊 "New" 按鈕，選擇 "Blueprint"

5. 連接您的 GitHub 倉庫

6. Render 將自動檢測 `render.yaml` 文件並設置服務

7. 填寫環境變數：
   - OPENAI_API_KEY: 您的 OpenAI API 密鑰

8. 點擊 "Apply" 按鈕

9. 等待部署完成，您的應用將在幾分鐘內上線

## Railway 部署

Railway 是一個開發者友好的平台，適合小型應用。

### 前置準備

1. 確保您有一個 [Railway](https://railway.app) 帳戶
2. 確保您的專案已經推送到 GitHub 倉庫

### 部署步驟

1. 在專案根目錄創建一個 `Procfile` 文件：

```
web: streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```

2. 將此文件提交並推送到 GitHub：
```bash
git add Procfile
git commit -m "添加 Railway 配置文件"
git push
```

3. 登入 [Railway Dashboard](https://railway.app)

4. 點擊 "New Project" 按鈕

5. 選擇 "Deploy from GitHub repo"

6. 連接您的 GitHub 倉庫

7. 在 "Variables" 選項卡中添加環境變數：
   - OPENAI_API_KEY: 您的 OpenAI API 密鑰

8. Railway 將自動部署您的應用

9. 點擊 "Settings" 選項卡，然後點擊 "Generate Domain" 生成一個公共 URL

## Heroku 部署

Heroku 是一個成熟的雲端平台，支援多種應用類型。

### 前置準備

1. 確保您有一個 [Heroku](https://heroku.com) 帳戶
2. 安裝 [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
3. 確保您的專案已經初始化為 Git 倉庫

### 部署步驟

1. 在專案根目錄創建一個 `Procfile` 文件：

```
web: streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0
```

2. 登入 Heroku CLI：
```bash
heroku login
```

3. 創建一個 Heroku 應用：
```bash
heroku create 你的應用名稱
```

4. 設置環境變數：
```bash
heroku config:set OPENAI_API_KEY=你的OpenAI密鑰
```

5. 部署應用：
```bash
git add .
git commit -m "準備 Heroku 部署"
git push heroku main
```

6. 打開應用：
```bash
heroku open
```

## 常見問題

### 1. 我的應用部署成功，但無法正常運行

- 檢查是否正確設置了所有必要的環境變數，特別是 OPENAI_API_KEY
- 檢查應用日誌以獲取錯誤信息
- 確保您的 OpenAI API 密鑰有足夠的額度

### 2. 我的應用運行緩慢

- 考慮升級到付費計劃以獲取更多資源
- 優化您的代碼和資源使用
- 減少向量存儲的大小或優化查詢

### 3. 我的文件無法上傳或保存

- 雲端平台通常使用臨時文件系統，不適合永久存儲
- 考慮使用外部存儲服務，如 AWS S3、Google Cloud Storage 等
- 在部署前上傳必要的文件到知識庫

### 4. 如何更新已部署的應用？

- 對於 Streamlit Cloud、Render 和 Railway，只需推送更改到 GitHub 倉庫
- 對於 Heroku，使用 `git push heroku main` 命令

### 5. 如何查看應用日誌？

- Streamlit Cloud: 在應用設置中點擊 "Manage app" 然後查看 "Logs" 選項卡
- Render: 在應用頁面點擊 "Logs" 選項卡
- Railway: 在應用頁面點擊 "Logs" 選項卡
- Heroku: 使用 `heroku logs --tail` 命令