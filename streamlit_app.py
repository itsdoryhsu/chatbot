#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import uuid
import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredURLLoader
)
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate
import re
import pandas as pd
from datetime import datetime
import yt_dlp
import requests

# 設置頁面配置
st.set_page_config(
    page_title="財務稅法QA機器人",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 初始化目錄
os.makedirs("data/documents", exist_ok=True)
os.makedirs("data/youtube", exist_ok=True)
os.makedirs("data/vectorstore", exist_ok=True)

# 初始化會話狀態
if "conversation" not in st.session_state:
    st.session_state.conversation = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "document_list" not in st.session_state:
    st.session_state.document_list = []
if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = ""
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gpt-3.5-turbo-16k"
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = """你是一個專業的財務稅法顧問，負責回答用戶的財務和稅法問題。

請遵循以下指導原則：
1. 使用繁體中文回答所有問題，即使用戶使用簡體中文提問。
2. 首先仔細分析用戶問題的真正意圖和語義，理解用戶真正想知道的是什麼。
3. 基於提供的文檔內容回答問題，但不要僅僅複製文檔中的內容。
4. 如果文檔中的信息不完整，請使用你的專業知識補充回答，但明確區分哪些是來自文檔的信息，哪些是你的專業補充。
5. 如果文檔中完全沒有相關信息，請誠實地說明，並提供你的專業建議或引導用戶尋找更多資源。
6. 回答應該專業、準確、易於理解，並引用相關的法規或文檔來源。
7. 對於會計、稅務等專業問題，請提供系統性的回答，而不僅僅是列出文檔中提到的片段。

記住：你的目標是真正解決用戶的問題，而不僅僅是檢索和呈現文檔內容。"""

# 側邊欄 - API設置
with st.sidebar:
    st.title("💼 財務稅法QA機器人")
    
    # API密鑰輸入
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key:
        st.session_state.openai_api_key = api_key
        os.environ["OPENAI_API_KEY"] = api_key
    
    # 模型選擇
    st.subheader("模型選擇")
    model_options = {
        "GPT-3.5 Turbo": "gpt-3.5-turbo-16k",
        "GPT-4o": "gpt-4o",
        "GPT-4.1 Turbo": "gpt-4-turbo",
        "GPT-4 Mini": "gpt-4-mini"
    }
    selected_model_name = st.selectbox(
        "選擇OpenAI模型",
        options=list(model_options.keys()),
        index=0
    )
    st.session_state.selected_model = model_options[selected_model_name]
    st.caption(f"當前選擇: {st.session_state.selected_model}")
    
    st.divider()
    
    # 系統提示設置
    st.subheader("系統提示設置")
    system_prompt = st.text_area(
        "自定義系統提示",
        value=st.session_state.system_prompt,
        height=150,
        help="這是給AI的指令，告訴它如何回答問題。您可以根據需要修改。"
    )
    st.session_state.system_prompt = system_prompt
    
    # 選擇頁面
    st.divider()
    st.subheader("導航")
    page = st.radio("選擇頁面", ["聊天對話", "知識庫管理"])

# 工具函數
def extract_youtube_id(url):
    """從YouTube URL中提取視頻ID"""
    youtube_regex = r"(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})"
    match = re.search(youtube_regex, url)
    return match.group(1) if match else None

def get_youtube_transcript(youtube_id):
    """獲取YouTube視頻的字幕"""
    try:
        youtube_url = f"https://www.youtube.com/watch?v={youtube_id}"
        
        # 使用yt_dlp獲取視頻信息
        with st.spinner("正在獲取YouTube字幕..."):
            with yt_dlp.YoutubeDL({}) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                subs = info.get('subtitles', {})
                auto_subs = info.get('automatic_captions', {})
                
                # 顯示可用的字幕語言
                all_langs = list(subs.keys()) + list(auto_subs.keys())
                if all_langs:
                    st.info(f"該視頻有以下語言的字幕可用: {', '.join(all_langs)}")
                
                # 優先手動字幕，其次自動字幕
                target = None
                source_type = None
                lang_found = None
                
                # 優先查找中文字幕
                for source, source_name in [(subs, "手動"), (auto_subs, "自動")]:
                    for lang, tracks in source.items():
                        if lang.startswith('zh'):
                            # 找到字幕網址
                            for track in tracks:
                                if track['ext'] == 'vtt':
                                    target = track['url']
                                    source_type = source_name
                                    lang_found = lang
                                    break
                        if target:
                            break
                    if target:
                        break
                
                # 如果沒有中文字幕，嘗試英文字幕
                if not target:
                    for source, source_name in [(subs, "手動"), (auto_subs, "自動")]:
                        for lang, tracks in source.items():
                            if lang.startswith('en'):
                                # 找到字幕網址
                                for track in tracks:
                                    if track['ext'] == 'vtt':
                                        target = track['url']
                                        source_type = source_name
                                        lang_found = lang
                                        break
                            if target:
                                break
                        if target:
                            break
                
                # 如果還是沒有，嘗試任何可用的字幕
                if not target and (subs or auto_subs):
                    for source, source_name in [(subs, "手動"), (auto_subs, "自動")]:
                        if source:
                            first_lang = list(source.keys())[0]
                            tracks = source[first_lang]
                            for track in tracks:
                                if track['ext'] == 'vtt':
                                    target = track['url']
                                    source_type = source_name
                                    lang_found = first_lang
                                    break
                            if target:
                                break
                
                if not target:
                    st.error("此影片沒有任何可用字幕")
                    return None
                
                st.success(f"找到{lang_found}字幕，來源：{source_type}")
                
                # 下載字幕內容
                r = requests.get(target)
                
                # 解析VTT格式字幕
                transcript = []
                for line in r.text.splitlines():
                    # 過濾掉VTT標頭、時間軸等
                    if line.strip() == "" or "-->" in line or line.startswith("WEBVTT"):
                        continue
                    transcript.append(line.strip())
                
                # 合併字幕文本
                return " ".join(transcript)
    except Exception as e:
        st.error(f"獲取YouTube字幕失敗: {str(e)}")
        return None

def get_youtube_info(youtube_id):
    """獲取YouTube視頻的信息"""
    try:
        youtube_url = f"https://www.youtube.com/watch?v={youtube_id}"
        
        # 使用yt_dlp獲取視頻信息
        with yt_dlp.YoutubeDL({}) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            
            return {
                "title": info.get('title', f"YouTube視頻 {youtube_id}"),
                "author": info.get('uploader', "YouTube作者"),
                "publish_date": info.get('upload_date'),
                "views": info.get('view_count', 0),
                "thumbnail_url": info.get('thumbnail') or f"https://img.youtube.com/vi/{youtube_id}/0.jpg"
            }
    except Exception as e:
        st.error(f"獲取YouTube信息失敗: {str(e)}")
        # 返回默認值
        return {
            "title": f"YouTube視頻 {youtube_id}",
            "author": "YouTube作者",
            "publish_date": None,
            "views": 0,
            "thumbnail_url": f"https://img.youtube.com/vi/{youtube_id}/0.jpg"
        }

def process_document(file, category, tags):
    """處理上傳的文檔"""
    # 生成唯一ID
    doc_id = str(uuid.uuid4())
    
    # 獲取文件擴展名
    file_extension = os.path.splitext(file.name)[1].lower()
    
    # 保存文件
    file_path = f"data/documents/{doc_id}{file_extension}"
    with open(file_path, "wb") as f:
        f.write(file.getbuffer())
    
    # 根據文件類型選擇加載器
    try:
        if file_extension == ".pdf":
            loader = PyPDFLoader(file_path)
        elif file_extension in [".docx", ".doc"]:
            loader = Docx2txtLoader(file_path)
        elif file_extension in [".txt", ".md", ".csv"]:
            loader = TextLoader(file_path)
        else:
            st.error(f"不支持的文件類型: {file_extension}")
            return None
        
        # 加載文檔
        documents = loader.load()
        
        # 添加元數據
        valid_documents = []
        for doc in documents:
            if hasattr(doc, 'metadata'):
                doc.metadata["source"] = file.name
                doc.metadata["doc_id"] = doc_id
                doc.metadata["category"] = category
                doc.metadata["tags"] = ",".join(tags) if isinstance(tags, list) else tags
                doc.metadata["date_added"] = datetime.now().isoformat()
                doc.metadata["type"] = "document"
                valid_documents.append(doc)
            else:
                st.warning(f"跳過無效的文檔: {type(doc)}")
        
        documents = valid_documents
        
        # 將文檔添加到文檔列表
        st.session_state.document_list.append({
            "id": doc_id,
            "name": file.name,
            "type": file_extension[1:],
            "category": category,
            "tags": tags,
            "date_added": datetime.now().isoformat(),
            "path": file_path
        })
        
        return documents
    except Exception as e:
        st.error(f"處理文檔失敗: {str(e)}")
        return None

def process_youtube(youtube_url, category, tags):
    """處理YouTube URL"""
    # 提取YouTube ID
    youtube_id = extract_youtube_id(youtube_url)
    if not youtube_id:
        st.error("無效的YouTube URL")
        return None
    
    # 獲取字幕
    transcript = get_youtube_transcript(youtube_id)
    if not transcript:
        st.error(f"無法獲取YouTube視頻 {youtube_id} 的字幕，請確保視頻有字幕")
        return None
    
    # 獲取YouTube信息（即使失敗也繼續）
    info = get_youtube_info(youtube_id)
    
    # 生成唯一ID
    doc_id = str(uuid.uuid4())
    
    # 保存字幕
    transcript_path = f"data/youtube/{doc_id}.txt"
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcript)
    
    # 創建文檔
    loader = TextLoader(transcript_path)
    documents = loader.load()
    
    # 添加元數據
    valid_documents = []
    for doc in documents:
        if hasattr(doc, 'metadata'):
            doc.metadata["source"] = info["title"]
            doc.metadata["doc_id"] = doc_id
            doc.metadata["youtube_id"] = youtube_id
            doc.metadata["youtube_url"] = youtube_url
            doc.metadata["category"] = category
            doc.metadata["tags"] = ",".join(tags) if isinstance(tags, list) else tags
            doc.metadata["date_added"] = datetime.now().isoformat()
            doc.metadata["type"] = "youtube"
            doc.metadata["author"] = info["author"]
            valid_documents.append(doc)
        else:
            st.warning(f"跳過無效的YouTube文檔: {type(doc)}")
    
    documents = valid_documents
    
    # 將文檔添加到文檔列表
    st.session_state.document_list.append({
        "id": doc_id,
        "name": info["title"],
        "type": "youtube",
        "category": category,
        "tags": tags,
        "date_added": datetime.now().isoformat(),
        "path": transcript_path,
        "youtube_id": youtube_id,
        "youtube_url": youtube_url,
        "thumbnail_url": info["thumbnail_url"]
    })
    
    st.success(f"成功添加YouTube視頻: {info['title']}")
    return documents

def update_vectorstore():
    """更新向量存儲"""
    if not st.session_state.openai_api_key:
        st.error("請先設置OpenAI API Key")
        return
    
    with st.spinner("正在更新知識庫..."):
        # 初始化嵌入模型
        embeddings = OpenAIEmbeddings()
        
        # 從文檔列表中加載所有文檔
        all_documents = []
        for doc_info in st.session_state.document_list:
            try:
                if doc_info["type"] == "youtube":
                    loader = TextLoader(doc_info["path"])
                elif doc_info["type"] == "pdf":
                    loader = PyPDFLoader(doc_info["path"])
                elif doc_info["type"] in ["doc", "docx"]:
                    loader = Docx2txtLoader(doc_info["path"])
                else:
                    loader = TextLoader(doc_info["path"])
                
                documents = loader.load()
                
                # 添加元數據
                valid_documents = []
                for doc in documents:
                    if hasattr(doc, 'metadata'):
                        doc.metadata["source"] = doc_info["name"]
                        doc.metadata["doc_id"] = doc_info["id"]
                        doc.metadata["category"] = doc_info["category"]
                        doc.metadata["tags"] = ",".join(doc_info["tags"]) if isinstance(doc_info["tags"], list) else doc_info["tags"]
                        doc.metadata["type"] = doc_info["type"]
                        valid_documents.append(doc)
                    else:
                        st.warning(f"跳過無效的文檔: {type(doc)}")
                
                all_documents.extend(valid_documents)
            except Exception as e:
                st.error(f"加載文檔 {doc_info['name']} 失敗: {str(e)}")
        
        if not all_documents:
            st.warning("沒有可用的文檔")
            return
        
        # 分割文檔
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_documents(all_documents)
        
        # 過濾複雜的元數據
        filtered_chunks = []
        for chunk in chunks:
            # 確保chunk是Document對象而不是字符串
            if hasattr(chunk, 'metadata'):
                # 手動過濾複雜的元數據
                for key in list(chunk.metadata.keys()):
                    value = chunk.metadata[key]
                    # 如果值是複雜類型（不是str、int、float或bool），則轉換或刪除
                    if not isinstance(value, (str, int, float, bool)):
                        if isinstance(value, list):
                            # 將列表轉換為字符串
                            chunk.metadata[key] = ",".join(map(str, value))
                        else:
                            # 刪除其他複雜類型
                            del chunk.metadata[key]
                
                filtered_chunks.append(chunk)
            else:
                st.warning(f"跳過無效的文檔塊: {type(chunk)}")
        
        # 使用過濾後的chunks
        chunks = filtered_chunks
        
        # 創建向量存儲
        st.session_state.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory="data/vectorstore"
        )
        
        # 創建提示模板
        system_template = st.session_state.system_prompt + """

文檔內容: {context}

請記住以下步驟來回答用戶的問題：
1. 仔細分析用戶問題的真正意圖和語義
2. 思考這個問題在財務稅法領域的專業背景和重要性
3. 從提供的文檔中找出相關信息
4. 組織一個結構化、系統性的回答，而不僅僅是列出文檔片段
5. 如有必要，補充專業知識以提供完整回答
6. 確保回答使用繁體中文，專業準確且易於理解
"""
        system_message_prompt = SystemMessagePromptTemplate.from_template(system_template)
        human_template = "{question}"
        human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
        
        # 組合提示模板
        chat_prompt = ChatPromptTemplate.from_messages([
            system_message_prompt,
            human_message_prompt
        ])
        
        # 初始化對話鏈
        st.session_state.conversation = ConversationalRetrievalChain.from_llm(
            llm=ChatOpenAI(
                temperature=0.7,  # 提高溫度以獲得更多樣化的回答
                model=st.session_state.selected_model  # 使用用戶選擇的模型
            ),
            combine_docs_chain_kwargs={"prompt": chat_prompt},  # 使用自定義提示模板
            retriever=st.session_state.vectorstore.as_retriever(
                search_kwargs={"k": 6}  # 檢索6個最相關的文檔片段
            ),
            memory=ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="answer"  # 明確指定要存儲的輸出鍵
            ),
            chain_type="stuff",  # 使用stuff方法將所有檢索到的文檔合併到一個提示中
            verbose=True,  # 啟用詳細日誌
            return_source_documents=True  # 返回源文檔以便調試
        )
        
        st.success(f"知識庫更新完成！共處理了 {len(chunks)} 個文本塊。")

def process_query(query):
    """處理用戶查詢"""
    if not st.session_state.conversation:
        st.error("請先更新知識庫")
        return
    
    with st.spinner("思考中..."):
        response = st.session_state.conversation({"question": query})
        answer = response["answer"]
        source_documents = response.get("source_documents", [])
        
        # 添加來源信息
        if source_documents:
            sources_text = "\n\n**參考來源：**\n"
            
            # 去重邏輯：使用集合記錄已經添加的文檔ID和內容
            added_sources = set()
            unique_docs = []
            
            for doc in source_documents:
                source = doc.metadata.get("source", "未知來源")
                doc_id = doc.metadata.get("doc_id", "")
                # 創建唯一標識，結合文檔ID和內容的前50個字符
                content_hash = f"{doc_id}_{doc.page_content[:50]}"
                
                # 如果這個來源還沒有添加過，則添加它
                if content_hash not in added_sources:
                    added_sources.add(content_hash)
                    unique_docs.append(doc)
            
            # 最多顯示3個不重複的來源
            for i, doc in enumerate(unique_docs[:3], 1):
                source = doc.metadata.get("source", "未知來源")
                doc_type = doc.metadata.get("type", "文件")
                category = doc.metadata.get("category", "")
                
                # 提取文檔片段的簡短摘要（最多100個字符）
                content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                
                # 確保使用繁體中文
                if doc_type == "youtube":
                    sources_text += f"{i}. YouTube影片：{source}\n   相關內容：「{content_preview}」\n"
                else:
                    sources_text += f"{i}. 文件：{source} (類別：{category})\n   相關內容：「{content_preview}」\n"
            
            # 將來源信息添加到回答中
            answer_with_sources = f"{answer}\n{sources_text}"
        else:
            answer_with_sources = answer
        
        st.session_state.chat_history.append({"role": "user", "content": query})
        st.session_state.chat_history.append({"role": "assistant", "content": answer_with_sources})
        
        return answer_with_sources

# 知識庫管理頁面
if page == "知識庫管理":
    st.header("📚 知識庫管理")
    
    # 創建選項卡
    tab1, tab2, tab3 = st.tabs(["📄 添加文檔", "🎬 添加YouTube", "🗂️ 管理知識庫"])
    
    # 添加文檔選項卡
    with tab1:
        st.subheader("上傳文檔")
        
        # 文檔上傳表單
        with st.form("document_upload_form"):
            uploaded_file = st.file_uploader("選擇文檔", type=["pdf", "docx", "txt", "md", "csv"])
            category = st.text_input("分類", "財務稅法")
            tags = st.text_input("標籤 (用逗號分隔)", "財務,稅法")
            
            submit_button = st.form_submit_button("上傳文檔")
            
            if submit_button and uploaded_file:
                documents = process_document(uploaded_file, category, tags.split(","))
                if documents:
                    st.success(f"文檔 '{uploaded_file.name}' 上傳成功！")
    
    # 添加YouTube選項卡
    with tab2:
        st.subheader("添加YouTube影片")
        
        # YouTube URL表單
        with st.form("youtube_form"):
            youtube_url = st.text_input("YouTube URL")
            category = st.text_input("分類", "財務稅法")
            tags = st.text_input("標籤 (用逗號分隔)", "財務,稅法")
            
            submit_button = st.form_submit_button("添加YouTube")
            
            if submit_button and youtube_url:
                documents = process_youtube(youtube_url, category, tags.split(","))
                if documents:
                    st.success(f"YouTube影片添加成功！")
    
    # 管理知識庫選項卡
    with tab3:
        st.subheader("知識庫內容")
        
        if st.session_state.document_list:
            # 創建數據框
            df = pd.DataFrame(st.session_state.document_list)
            df = df[["name", "type", "category", "tags", "date_added"]]
            df.columns = ["名稱", "類型", "分類", "標籤", "添加日期"]
            
            # 顯示數據框
            st.dataframe(df, use_container_width=True)
            
            # 刪除文檔
            if st.button("刪除選中的文檔"):
                st.warning("此功能尚未實現")
        else:
            st.info("知識庫中沒有文檔")
        
        # 更新向量存儲
        if st.button("更新知識庫"):
            update_vectorstore()

# 聊天對話頁面
elif page == "聊天對話":
    st.header("💬 財務稅法助手")
    
    # 檢查是否設置了API密鑰
    if not st.session_state.openai_api_key:
        st.warning("請在側邊欄設置OpenAI API Key")
        st.stop()
    
    # 檢查是否有文檔
    if not st.session_state.document_list:
        st.warning("請先在知識庫管理頁面添加文檔")
        st.stop()
    
    # 檢查是否初始化了向量存儲
    if not st.session_state.vectorstore:
        st.info("請先更新知識庫")
        if st.button("更新知識庫"):
            update_vectorstore()
        st.stop()
    
    # 顯示聊天歷史
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # 聊天輸入
    user_query = st.chat_input("請輸入您的問題...")
    if user_query:
        # 顯示用戶消息
        with st.chat_message("user"):
            st.write(user_query)
        
        # 獲取回答
        answer = process_query(user_query)
        
        # 顯示助手消息
        with st.chat_message("assistant"):
            st.write(answer)

# 頁腳
st.sidebar.divider()
st.sidebar.caption("© 2025 財務稅法QA機器人 | 版本 0.1.0")