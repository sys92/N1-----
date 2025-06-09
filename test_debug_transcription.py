import requests
import os
import time
import threading

def test_debug_transcription():
    """
    デバッグエンドポイントで文字起こしをテスト
    """
    # テストファイルのパス（20分のファイル）
    audio_file_path = r"C:\Users\sasak\Desktop\N1インタビュー_cut_00.wav"
    
    if not os.path.exists(audio_file_path):
        print(f"❌ テストファイルが見つかりません: {audio_file_path}")
        return
    
    file_size = os.path.getsize(audio_file_path)
    print(f"📁 テストファイル: {audio_file_path}")
    print(f"📊 ファイルサイズ: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    
    # セッションIDを生成
    session_id = f"debug_test_{int(time.time())}"
    print(f"🔑 セッションID: {session_id}")
    
    try:
        # 本番テスト: 完全なシステム（分析付き）を使用
        url = "http://localhost:8000/analyze"
        
        print("🚀 本番システム（文字起こし+分析）リクエスト送信中...")
        print("📡 リクエスト送信完了 - サーバーでの処理開始...")

        start_time = time.time()

        # 進捗表示用のフラグ
        processing = True

        def show_progress():
            """処理中の進捗を表示"""
            dots = 0
            while processing:
                elapsed = time.time() - start_time
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                dot_str = "." * (dots % 4)
                print(f"\r⏳ 処理中{dot_str:<3} ({minutes:02d}:{seconds:02d})", end="", flush=True)
                time.sleep(1)
                dots += 1

        # 進捗表示を別スレッドで開始
        progress_thread = threading.Thread(target=show_progress)
        progress_thread.daemon = True
        progress_thread.start()

        try:
            with open(audio_file_path, 'rb') as f:
                files = {'audio_file': (os.path.basename(audio_file_path), f, 'audio/wav')}
                data = {'session_id': session_id}

                response = requests.post(url, files=files, data=data, timeout=3600)
        finally:
            processing = False
            print()  # 改行
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️ 処理時間: {processing_time:.1f}秒 ({processing_time/60:.1f}分)")
        print(f"📡 レスポンスステータス: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 本番システム分析成功!")
            result = response.json()

            # 完全なシステムの結果を表示
            analysis = result.get('analysis', '')
            transcription = result.get('full_transcription', '')
            success = result.get('success', False)

            print(f"\n📊 本番システム結果:")
            print(f"  成功: {success}")
            print(f"  分析結果の長さ: {len(analysis):,} 文字")
            print(f"  文字起こしの長さ: {len(transcription):,} 文字")
            
            # 時間範囲を分析
            lines = transcription.split('\n')
            timestamps = []
            
            for line in lines:
                if '【' in line and '】' in line:
                    try:
                        timestamp_str = line.split('【')[1].split('】')[0]
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
                
                print(f"\n⏰ 時間範囲:")
                print(f"  開始時刻: {min_time//3600:02d}:{(min_time%3600)//60:02d}:{min_time%60:02d}")
                print(f"  終了時刻: {max_time//3600:02d}:{(max_time%3600)//60:02d}:{max_time%60:02d}")
                print(f"  処理された時間: {duration_minutes:.1f}分")
                print(f"  タイムスタンプ数: {len(timestamps)}")
                
                # 期待値との比較
                expected_duration = 50
                coverage = (duration_minutes / expected_duration) * 100
                print(f"  カバレッジ: {coverage:.1f}% (期待: {expected_duration}分)")
                
                if coverage < 80:
                    print(f"  ❌ カバレッジが低すぎます")
                else:
                    print(f"  ✅ カバレッジは適切です")
            
            # 分析結果のサンプル表示
            print(f"\n📊 N1分析結果サンプル（最初の500文字）:")
            print(analysis[:500])
            if len(analysis) > 500:
                print("...")

            # 文字起こしサンプル表示
            print(f"\n📝 文字起こし最初の5行:")
            for i, line in enumerate(lines[:5]):
                if line.strip():
                    print(f"  {line}")

            print(f"\n📝 文字起こし最後の5行:")
            for line in lines[-5:]:
                if line.strip():
                    print(f"  {line}")
            
        else:
            print(f"❌ 本番システム分析失敗: {response.text}")

    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    print("🎯 本番システム完全テスト開始")
    print("="*60)
    test_debug_transcription()
    print("\n🎯 本番テスト完了")
