# 財務稅法QA機器人

這是一個基於RAG（檢索增強生成）技術的財務稅法問答系統，允許用戶添加多種知識來源，並通過對話界面解決財務稅法問題。

## 功能特點

- **彈性知識庫管理**：
  - 支持多種文檔類型（PDF、Word、文本等）
  - 支持YouTube影片內容提取
  - 文檔分類和標記系統
  - 知識庫內容管理界面

- **基於RAG的問答系統**：
  - 使用LangChain框架處理RAG流程
  - 使用Chroma作為向量數據庫
  - 整合OpenAI語言模型生成回答

- **簡潔直觀的用戶界面**：
  - 使用Streamlit構建的網頁界面
  - 聊天對話頁面
  - 知識庫管理頁面

## 安裝步驟

1. 克隆此存儲庫：
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. 安裝依賴項：
   ```
   pip install -r requirements.txt
   ```

3. 創建 `.env` 文件並設置OpenAI API密鑰：
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```

## 使用方法

1. 啟動Streamlit應用：
   ```
   streamlit run streamlit_app.py
   ```

2. 在瀏覽器中打開應用（通常是 http://localhost:8501）

3. 在側邊欄輸入您的OpenAI API密鑰

4. 切換到「知識庫管理」頁面，添加文檔或YouTube影片

5. 點擊「更新知識庫」按鈕，處理添加的知識來源

6. 切換到「聊天對話」頁面，開始提問

## 知識來源支持

- **文檔類型**：
  - PDF文件 (.pdf)
  - Word文檔 (.docx, .doc)
  - 文本文件 (.txt, .md)
  - CSV文件 (.csv)

- **YouTube影片**：
  - 自動提取字幕內容
  - 支持中文和英文字幕

## 系統要求

- Python 3.8+
- OpenAI API密鑰
- 網絡連接（用於訪問OpenAI API和YouTube）

## 未來改進

- 添加更多文檔類型支持
- 支持網頁內容抓取
- 添加LINE機器人整合
- 改進文檔處理和分割算法
- 添加用戶認證和多用戶支持
- 添加知識庫版本控制

## 授權

[MIT License](LICENSE)