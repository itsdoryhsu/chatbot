#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import webbrowser
from time import sleep

def main():
    """啟動財務稅法QA機器人"""
    print("=" * 50)
    print("財務稅法QA機器人啟動器")
    print("=" * 50)
    
    # 檢查環境變數
    if not os.path.exists(".env") and os.path.exists(".env.example"):
        print("未找到.env文件，正在從.env.example創建...")
        with open(".env.example", "r", encoding="utf-8") as example_file:
            example_content = example_file.read()
        
        with open(".env", "w", encoding="utf-8") as env_file:
            env_file.write(example_content)
        
        print("已創建.env文件，請編輯此文件並設置您的API密鑰")
        print("按Enter鍵繼續...")
        input()
    
    # 創建必要的目錄
    os.makedirs("data/documents", exist_ok=True)
    os.makedirs("data/youtube", exist_ok=True)
    os.makedirs("data/vectorstore", exist_ok=True)
    
    print("正在啟動Streamlit應用...")
    
    # 啟動Streamlit應用
    port = os.getenv("PORT", "8501")
    url = f"http://localhost:{port}"
    
    # 嘗試打開瀏覽器
    try:
        webbrowser.open(url)
        print(f"已在瀏覽器中打開應用: {url}")
    except:
        print(f"無法自動打開瀏覽器，請手動訪問: {url}")
    
    # 啟動Streamlit
    subprocess.run(["streamlit", "run", "streamlit_app.py"])

if __name__ == "__main__":
    main()