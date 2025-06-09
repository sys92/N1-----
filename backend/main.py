from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, Form, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
import logging
from dotenv import load_dotenv

from services.transcription import TranscriptionService
from services.analysis import AnalysisService
from services.progress_manager import progress_manager
from models.schemas import AnalysisResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="N1インタビュー分析API",
    description="N1インタビューの音声データを自動で分析するAPI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
transcription_service = TranscriptionService()
analysis_service = AnalysisService()

@app.get("/")
async def root():
    return {"message": "N1インタビュー分析API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    print(f"🔌 [WEBSOCKET] 接続要求: {session_id}")
    await websocket.accept()
    print(f"✅ [WEBSOCKET] 接続確立: {session_id}")
    await progress_manager.add_connection(session_id, websocket)

    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"🔌 [WEBSOCKET] 切断: {session_id}")
        await progress_manager.remove_connection(session_id, websocket)

@app.post("/debug_transcription")
async def debug_transcription(audio_file: UploadFile = File(...), session_id: str = Form("default")):
    """
    デバッグ用: 文字起こしのみを実行（分析なし）
    """
    logger.info(f"DEBUG: Received file: {audio_file.filename}, type: {audio_file.content_type}")

    # 進捗開始
    print(f"🚀 [PROGRESS] 5% - ファイルアップロード完了 (ファイル: {audio_file.filename})")
    await progress_manager.update_progress(session_id, "upload", 5, "ファイルアップロード完了")

    # ファイル検証（簡略化）
    content = await audio_file.read()
    logger.info(f"DEBUG: File size: {len(content)} bytes")

    await progress_manager.update_progress(session_id, "validation", 10, "ファイル検証完了")

    try:
        # 一時ファイルに保存
        file_extension = ".wav"
        if audio_file.filename:
            file_extension = os.path.splitext(audio_file.filename)[1] or ".wav"

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            logger.info("DEBUG: Starting transcription...")
            # 文字起こしのみ実行
            transcription_result = await transcription_service.transcribe(temp_file_path, session_id)
            logger.info("DEBUG: Transcription completed")

            await progress_manager.update_progress(session_id, "completed", 100, "文字起こし完了！")

            return {
                "success": True,
                "transcription": transcription_result.full_text,
                "segment_count": len(transcription_result.segments),
                "debug_info": f"Processed {len(transcription_result.segments)} segments"
            }

        finally:
            # 一時ファイルを削除
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except Exception as e:
        logger.error(f"DEBUG: Transcription failed: {str(e)}", exc_info=True)
        await progress_manager.update_progress(session_id, "error", 0, f"エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

@app.post("/analyze")
async def analyze_audio(audio_file: UploadFile = File(...), session_id: str = Form("default")):
    """
    音声ファイルを受け取り、文字起こしと分析を実行する
    """
    print(f"📥 [REQUEST] リクエスト受信: {audio_file.filename} (セッション: {session_id})")
    logger.info(f"Received file: {audio_file.filename}, type: {audio_file.content_type}")

    # 進捗開始
    await progress_manager.update_progress(session_id, "upload", 5, "ファイルアップロード完了")

    # Validate file type
    allowed_types = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/m4a"]
    if audio_file.content_type not in allowed_types:
        logger.error(f"Unsupported file type: {audio_file.content_type}")
        await progress_manager.update_progress(session_id, "error", 0, f"未対応のファイル形式: {audio_file.content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {audio_file.content_type}"
        )
    
    # Validate file size (1GB limit)
    max_size = 1024 * 1024 * 1024  # 1GB
    print(f"📖 [REQUEST] ファイル読み込み中...")
    content = await audio_file.read()
    print(f"✅ [REQUEST] ファイル読み込み完了: {len(content)} bytes ({len(content)/1024/1024:.1f}MB)")
    logger.info(f"File size: {len(content)} bytes")

    if len(content) > max_size:
        logger.error(f"File size exceeds limit: {len(content)} bytes")
        await progress_manager.update_progress(session_id, "error", 0, "ファイルサイズが1GB制限を超えています")
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 1GB limit"
        )

    print(f"🔍 [PROGRESS] 10% - ファイル検証完了 (サイズ: {len(content)/1024/1024:.1f}MB)")
    await progress_manager.update_progress(session_id, "validation", 10, "ファイル検証完了")
    
    try:
        # Save uploaded file temporarily with correct extension
        file_extension = ".mp3"  # Default to mp3
        if audio_file.filename:
            file_extension = os.path.splitext(audio_file.filename)[1] or ".mp3"

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            print(f"🎤 [PROGRESS] 15% - 音声の文字起こしを開始...")
            await progress_manager.update_progress(session_id, "transcription", 15, "音声の文字起こしを開始...")
            logger.info("Starting transcription...")
            # Step 1: Transcribe audio to text
            transcription_result = await transcription_service.transcribe(temp_file_path, session_id)
            print(f"✅ [PROGRESS] 78% - 音声認識完了 (セグメント数: {len(transcription_result.segments)})")
            logger.info("Transcription completed")

            print(f"🤖 [PROGRESS] 80% - AI分析を開始...")
            await progress_manager.update_progress(session_id, "analysis", 80, "AI分析を開始...")
            logger.info("Starting analysis...")
            # Step 2: Analyze transcription with Groq API
            analysis_result = await analysis_service.analyze(transcription_result)
            print(f"🎉 [PROGRESS] 100% - 分析完了！")
            logger.info("Analysis completed")

            await progress_manager.update_progress(session_id, "completed", 100, "分析完了！")

            return AnalysisResponse(
                success=True,
                analysis=analysis_result,
                transcription=transcription_result,
                full_transcription=transcription_result.full_text
            )
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        await progress_manager.update_progress(session_id, "error", 0, f"分析エラー: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    import sys

    # コンソール出力を強制的に有効化
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

    print("🚀 N1インタビュー分析API起動中...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
