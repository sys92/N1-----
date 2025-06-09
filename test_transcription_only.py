import requests
import os
import time
import json

def test_transcription_only():
    """
    分割→文字起こし→マージのテスト（分析は除外）
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
    session_id = f"transcription_test_{int(time.time())}"
    print(f"🔑 セッションID: {session_id}")
    
    try:
        # 文字起こしのみのエンドポイントを作成する必要があるが、
        # 今は既存のエンドポイントを使用
        url = "http://localhost:8000/analyze"
        
        print("🚀 文字起こしリクエスト送信中...")
        start_time = time.time()
        
        with open(audio_file_path, 'rb') as f:
            files = {'audio_file': (os.path.basename(audio_file_path), f, 'audio/wav')}
            data = {'session_id': session_id}
            
            response = requests.post(url, files=files, data=data, timeout=3600)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"⏱️ 処理時間: {processing_time:.1f}秒 ({processing_time/60:.1f}分)")
        print(f"📡 レスポンスステータス: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 文字起こし成功!")
            result = response.json()
            
            # 文字起こし結果の詳細分析
            transcription = result.get('full_transcription', '')
            
            print(f"\n📊 文字起こし結果分析:")
            print(f"  文字起こしの長さ: {len(transcription):,} 文字")
            
            # 文字起こしの時間範囲を分析
            lines = transcription.split('\n')
            timestamps = []
            
            print(f"\n⏰ タイムスタンプ分析:")
            print(f"  総行数: {len(lines)}")
            
            for line_num, line in enumerate(lines):
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
                            timestamps.append((total_seconds, line_num, line))
                    except Exception as e:
                        print(f"  ⚠️ タイムスタンプ解析エラー (行{line_num+1}): {e}")
                        continue
            
            if timestamps:
                # タイムスタンプの順序をチェック
                timestamps.sort(key=lambda x: x[0])  # 時間でソート
                
                min_time = timestamps[0][0]
                max_time = timestamps[-1][0]
                duration_minutes = (max_time - min_time) / 60
                
                print(f"  タイムスタンプ数: {len(timestamps)}")
                print(f"  開始時刻: {min_time//3600:02d}:{(min_time%3600)//60:02d}:{min_time%60:02d}")
                print(f"  終了時刻: {max_time//3600:02d}:{(max_time%3600)//60:02d}:{max_time%60:02d}")
                print(f"  処理された音声時間: {duration_minutes:.1f}分")
                
                # 順序の問題をチェック
                print(f"\n🔍 順序チェック:")
                order_issues = 0
                for i in range(1, len(timestamps)):
                    if timestamps[i][0] < timestamps[i-1][0]:
                        order_issues += 1
                        print(f"  ❌ 順序問題 {order_issues}: 行{timestamps[i][1]+1} ({timestamps[i][0]}s) < 行{timestamps[i-1][1]+1} ({timestamps[i-1][0]}s)")
                
                if order_issues == 0:
                    print(f"  ✅ タイムスタンプの順序は正常です")
                else:
                    print(f"  ❌ {order_issues}個の順序問題が見つかりました")
                
                # 重複内容のチェック
                print(f"\n🔍 重複チェック:")
                text_segments = [line.split('】')[1] if '】' in line else line for _, _, line in timestamps]
                unique_segments = set(text_segments)
                duplicate_count = len(text_segments) - len(unique_segments)
                
                print(f"  総セグメント数: {len(text_segments)}")
                print(f"  ユニークセグメント数: {len(unique_segments)}")
                print(f"  重複セグメント数: {duplicate_count}")
                
                if duplicate_count > len(text_segments) * 0.1:  # 10%以上重複
                    print(f"  ⚠️ 重複が多すぎます ({duplicate_count/len(text_segments)*100:.1f}%)")
                else:
                    print(f"  ✅ 重複は許容範囲内です ({duplicate_count/len(text_segments)*100:.1f}%)")
            
            # 最初と最後のサンプルを表示
            print(f"\n📝 文字起こしサンプル:")
            print(f"最初の10行:")
            for i, line in enumerate(lines[:10]):
                if line.strip():
                    print(f"  {i+1:2d}: {line}")
            
            print(f"\n最後の10行:")
            for i, line in enumerate(lines[-10:]):
                if line.strip():
                    print(f"  {len(lines)-10+i+1:2d}: {line}")
            
        else:
            print(f"❌ 文字起こし失敗: {response.text}")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    print("🧪 文字起こし専用テスト開始")
    print("="*60)
    test_transcription_only()
    print("\n🧪 テスト完了")
