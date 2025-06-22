#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 主程式入口點，用於啟動 LINE Bot
from line_chatbot.app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
