import asyncio
import json
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)

class ProgressManager:
    def __init__(self):
        self.connections: Dict[str, Set] = {}
        self.progress_data: Dict[str, dict] = {}
    
    async def add_connection(self, session_id: str, websocket):
        """WebSocket接続を追加"""
        if session_id not in self.connections:
            self.connections[session_id] = set()
        self.connections[session_id].add(websocket)
        print(f"🔗 [WEBSOCKET] 接続追加: {session_id} (接続数: {len(self.connections[session_id])})")
        logger.info(f"Added connection for session {session_id}")
    
    async def remove_connection(self, session_id: str, websocket):
        """WebSocket接続を削除"""
        if session_id in self.connections:
            self.connections[session_id].discard(websocket)
            if not self.connections[session_id]:
                del self.connections[session_id]
                if session_id in self.progress_data:
                    del self.progress_data[session_id]
        logger.info(f"Removed connection for session {session_id}")
    
    async def update_progress(self, session_id: str, stage: str, progress: int, message: str = ""):
        """進捗を更新してクライアントに送信"""
        progress_info = {
            "stage": stage,
            "progress": progress,
            "message": message,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        self.progress_data[session_id] = progress_info
        
        # 接続中のクライアントに送信
        if session_id in self.connections:
            print(f"📤 [WEBSOCKET] 送信準備: {session_id} (接続数: {len(self.connections[session_id])})")
            disconnected = set()
            for websocket in self.connections[session_id]:
                try:
                    await websocket.send_text(json.dumps(progress_info))
                    # WebSocketの送信を強制的にフラッシュ
                    if hasattr(websocket, 'transport') and hasattr(websocket.transport, 'write'):
                        try:
                            await websocket.transport.drain()
                        except:
                            pass
                    # 送信成功をログ出力
                    print(f"📡 [WEBSOCKET] Sent to client: {progress}% - {stage} - {message}")
                except Exception as e:
                    logger.error(f"Failed to send progress to websocket: {e}")
                    disconnected.add(websocket)
            
            # 切断されたWebSocketを削除
            for ws in disconnected:
                await self.remove_connection(session_id, ws)
        
        logger.info(f"Progress updated for {session_id}: {stage} - {progress}% - {message}")
        print(f"📊 [PROGRESS] {progress}% - {stage} - {message}")

# グローバルインスタンス
progress_manager = ProgressManager()
