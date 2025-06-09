from pydub import AudioSegment
import os

def check_audio_file():
    """
    音声ファイルの詳細情報を直接確認
    """
    audio_file_path = r"C:\Users\sasak\Desktop\N1tool_test\N1インタビュー_cut_00.wav"
    
    print(f"🔍 音声ファイル検証")
    print(f"ファイルパス: {audio_file_path}")
    
    # ファイル存在確認
    if not os.path.exists(audio_file_path):
        print(f"❌ ファイルが見つかりません")
        return
    
    # ファイルサイズ確認
    file_size = os.path.getsize(audio_file_path)
    print(f"ファイルサイズ: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
    
    try:
        print(f"\n📊 pydubで音声ファイルを読み込み中...")
        
        # 音声ファイルを読み込み
        audio = AudioSegment.from_file(audio_file_path)
        
        # 詳細情報を表示
        duration_ms = len(audio)
        duration_seconds = duration_ms / 1000.0
        duration_minutes = duration_seconds / 60.0
        
        print(f"✅ 読み込み成功!")
        print(f"")
        print(f"🎵 音声情報:")
        print(f"  時間: {duration_ms:,}ms")
        print(f"  時間: {duration_seconds:.1f}秒")
        print(f"  時間: {duration_minutes:.1f}分")
        print(f"  サンプルレート: {audio.frame_rate:,}Hz")
        print(f"  チャンネル数: {audio.channels}")
        print(f"  サンプル幅: {audio.sample_width} bytes")
        print(f"  フレーム数: {audio.frame_count():,}")
        
        # 期待値との比較
        expected_minutes = 50
        if duration_minutes < expected_minutes * 0.8:
            print(f"")
            print(f"⚠️  警告: 音声時間が短すぎます")
            print(f"  期待: {expected_minutes}分")
            print(f"  実際: {duration_minutes:.1f}分")
            print(f"  差異: {expected_minutes - duration_minutes:.1f}分")
        else:
            print(f"")
            print(f"✅ 音声時間は適切です")
        
        # 分割シミュレーション
        segment_duration = 2 * 60 * 1000  # 2分
        overlap_duration = 15 * 1000      # 15秒
        
        num_segments = math.ceil(duration_ms / segment_duration)
        
        print(f"")
        print(f"📐 分割シミュレーション:")
        print(f"  セグメント長: {segment_duration/1000:.0f}秒")
        print(f"  重複時間: {overlap_duration/1000:.0f}秒")
        print(f"  予想セグメント数: {num_segments}")
        
        # 最初の3セグメントの詳細
        print(f"")
        print(f"📋 最初の3セグメントの詳細:")
        for i in range(min(3, num_segments)):
            start_time = i * segment_duration
            end_time = min(start_time + segment_duration + overlap_duration, duration_ms)
            
            start_min = start_time / 1000 / 60
            end_min = end_time / 1000 / 60
            segment_duration_actual = (end_time - start_time) / 1000 / 60
            
            print(f"  セグメント {i+1}: {start_min:.1f}分 - {end_min:.1f}分 (長さ: {segment_duration_actual:.1f}分)")
        
        if num_segments > 3:
            print(f"  ... (残り{num_segments-3}セグメント)")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import math
    check_audio_file()
