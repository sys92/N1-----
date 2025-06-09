#!/usr/bin/env python3
"""
N1インタビュー分析システム バックエンド起動スクリプト
"""

import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
