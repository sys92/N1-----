import asyncio
import websockets
import json
import requests
import os
import threading
import time

def test_progress_tracking():
    """
    プログレスバーの進捗状況をテストする
    """
    # テストファイルのパス（小さなファイルで疑似進捗をテスト）
    audio_file_path = r"C:\Users\sasak\Desktop\N1tool_test\test-captain.mp3"
    
    if not os.path.exists(audio_file_path):
        print(f"❌ テストファイルが見つかりません: {audio_file_path}")
        return
    
    print(f"📁 テストファイル: {audio_file_path}")
    print(f"📊 ファイルサイズ: {os.path.getsize(audio_file_path)} bytes")
    
    # セッションIDを生成
    session_id = f"test_session_{int(time.time())}"
    print(f"🔑 セッションID: {session_id}")
    
    # WebSocket接続でプログレスを監視
    progress_data = []
    websocket_connected = False
    
    async def monitor_progress():
        nonlocal websocket_connected, progress_data
        
        try:
            uri = f"ws://localhost:8000/ws/{session_id}"
            print(f"🔌 WebSocket接続開始: {uri}")
            
            async with websockets.connect(uri) as websocket:
                websocket_connected = True
                print("✅ WebSocket接続成功")
                
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        progress_data.append(data)
                        
                        print(f"📈 進捗更新: {data['stage']} - {data['progress']}% - {data['message']}")
                        
                        # 完了またはエラーで終了
                        if data['stage'] in ['completed', 'error']:
                            break
                            
                    except asyncio.TimeoutError:
                        continue
                    except websockets.exceptions.ConnectionClosed:
                        print("🔌 WebSocket接続が閉じられました")
                        break
                        
        except Exception as e:
            print(f"❌ WebSocket接続エラー: {e}")
    
    # WebSocketを別スレッドで開始
    def run_websocket():
        asyncio.run(monitor_progress())
    
    websocket_thread = threading.Thread(target=run_websocket)
    websocket_thread.daemon = True
    websocket_thread.start()
    
    # WebSocket接続を待機
    timeout = 10
    start_time = time.time()
    while not websocket_connected and (time.time() - start_time) < timeout:
        time.sleep(0.1)
    
    if not websocket_connected:
        print("❌ WebSocket接続がタイムアウトしました")
        return
    
    print("🚀 分析リクエスト送信中...")
    
    # 分析リクエストを送信
    try:
        url = "http://localhost:8000/analyze"
        
        with open(audio_file_path, 'rb') as f:
            files = {'audio_file': (os.path.basename(audio_file_path), f, 'audio/mpeg')}
            data = {'session_id': session_id}
            
            response = requests.post(url, files=files, data=data, timeout=1800)  # 30分のタイムアウト
        
        print(f"📡 レスポンスステータス: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 分析成功!")
            result = response.json()
            print(f"📝 分析結果の長さ: {len(result.get('analysis', ''))}")
        else:
            print(f"❌ 分析失敗: {response.text}")
            
    except Exception as e:
        print(f"❌ リクエストエラー: {e}")
    
    # 少し待ってからプログレスデータを分析
    time.sleep(2)
    
    print("\n" + "="*50)
    print("📊 プログレス分析結果")
    print("="*50)
    
    if not progress_data:
        print("❌ プログレスデータが取得できませんでした")
        return
    
    print(f"📈 総プログレス更新回数: {len(progress_data)}")
    
    # 各段階の進捗を表示
    stages = {}
    for data in progress_data:
        stage = data['stage']
        if stage not in stages:
            stages[stage] = []
        stages[stage].append(data['progress'])
    
    print("\n🎯 段階別進捗:")
    for stage, progresses in stages.items():
        min_progress = min(progresses)
        max_progress = max(progresses)
        print(f"  {stage}: {min_progress}% → {max_progress}% ({len(progresses)}回更新)")
    
    # 進捗の連続性をチェック
    print("\n📈 進捗の推移:")
    for i, data in enumerate(progress_data):
        timestamp = data.get('timestamp', 0)
        print(f"  {i+1:2d}. {data['progress']:3d}% | {data['stage']:12s} | {data['message']}")
    
    # 進捗の妥当性をチェック
    print("\n✅ 進捗チェック:")
    
    # 進捗が増加しているかチェック
    progresses = [data['progress'] for data in progress_data if data['stage'] != 'error']
    if progresses:
        is_increasing = all(progresses[i] <= progresses[i+1] for i in range(len(progresses)-1))
        print(f"  進捗増加: {'✅' if is_increasing else '❌'}")
        print(f"  最終進捗: {progresses[-1]}%")
    
    # 期待される段階が含まれているかチェック
    expected_stages = ['upload', 'validation', 'transcribing', 'transcription_complete', 'analysis', 'completed']
    found_stages = set(data['stage'] for data in progress_data)
    
    print(f"  期待段階: {expected_stages}")
    print(f"  実際段階: {list(found_stages)}")
    
    missing_stages = set(expected_stages) - found_stages
    if missing_stages:
        print(f"  ❌ 不足段階: {missing_stages}")
    else:
        print(f"  ✅ 全段階完了")

if __name__ == "__main__":
    print("🧪 プログレス追跡テスト開始")
    print("="*50)
    test_progress_tracking()
    print("\n🧪 テスト完了")
