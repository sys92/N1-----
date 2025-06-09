import requests
import os
import time

def debug_audio_processing():
    """
    音声処理のデバッグ用テスト
    """
    # テストファイルのパス
    audio_file_path = r"C:\Users\sasak\Desktop\N1tool_test\N1インタビュー_cut.wav"
    
    if not os.path.exists(audio_file_path):
        print(f"❌ テストファイルが見つかりません: {audio_file_path}")
        return
    
    file_size = os.path.getsize(audio_file_path)
    print(f"📁 テストファイル: {audio_file_path}")
    print(f"📊 ファイルサイズ: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    
    # セッションIDを生成
    session_id = f"debug_session_{int(time.time())}"
    print(f"🔑 セッションID: {session_id}")
    
    try:
        url = "http://localhost:8000/analyze"
        
        print("🚀 分析リクエスト送信中...")
        start_time = time.time()
        
        with open(audio_file_path, 'rb') as f:
            files = {'audio_file': (os.path.basename(audio_file_path), f, 'audio/wav')}
            data = {'session_id': session_id}
            
            response = requests.post(url, files=files, data=data, timeout=3600)  # 1時間のタイムアウト
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️ 処理時間: {processing_time:.1f}秒 ({processing_time/60:.1f}分)")
        print(f"📡 レスポンスステータス: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 分析成功!")
            result = response.json()
            
            # 結果の詳細分析
            analysis = result.get('analysis', '')
            transcription = result.get('full_transcription', '')
            
            print(f"\n📊 結果分析:")
            print(f"  分析結果の長さ: {len(analysis):,} 文字")
            print(f"  文字起こしの長さ: {len(transcription):,} 文字")
            
            # 文字起こしの時間範囲を分析
            lines = transcription.split('\n')
            timestamps = []
            
            for line in lines:
                if '【' in line and '】' in line:
                    try:
                        timestamp_str = line.split('【')[1].split('】')[0]
                        # HH:MM:SS形式をパース
                        time_parts = timestamp_str.split(':')
                        if len(time_parts) == 3:
                            hours = int(time_parts[0])
                            minutes = int(time_parts[1])
                            seconds = int(time_parts[2])
                            total_seconds = hours * 3600 + minutes * 60 + seconds
                            timestamps.append(total_seconds)
                    except:
                        continue
            
            if timestamps:
                min_time = min(timestamps)
                max_time = max(timestamps)
                duration_minutes = (max_time - min_time) / 60
                
                print(f"\n⏰ 時間範囲分析:")
                print(f"  開始時刻: {min_time//3600:02d}:{(min_time%3600)//60:02d}:{min_time%60:02d}")
                print(f"  終了時刻: {max_time//3600:02d}:{(max_time%3600)//60:02d}:{max_time%60:02d}")
                print(f"  処理された音声時間: {duration_minutes:.1f}分")
                print(f"  タイムスタンプ数: {len(timestamps)}")
                
                # 期待される時間と比較
                expected_duration = 50  # 50分と予想
                if duration_minutes < expected_duration * 0.8:
                    print(f"⚠️  警告: 処理された時間が短すぎます（期待: {expected_duration}分, 実際: {duration_minutes:.1f}分）")
                else:
                    print(f"✅ 処理時間は適切です")
            
            # 文字起こしのサンプルを表示
            print(f"\n📝 文字起こしサンプル（最初の500文字）:")
            print(transcription[:500])
            print("...")
            
            print(f"\n📝 文字起こしサンプル（最後の500文字）:")
            print("...")
            print(transcription[-500:])
            
        else:
            print(f"❌ 分析失敗: {response.text}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    print("🔍 音声処理デバッグテスト開始")
    print("="*60)
    debug_audio_processing()
    print("\n🔍 デバッグテスト完了")
