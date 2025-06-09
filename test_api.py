#!/usr/bin/env python3
"""
API テストスクリプト
"""
import requests
import os

def test_analyze_api():
    """音声分析APIをテストする"""
    
    # テストファイルのパス（大きなWAVファイルの分割テスト）
    audio_file_path = r"C:\Users\sasak\Desktop\N1インタビュー_cut.wav"
    
    # ファイルの存在確認
    if not os.path.exists(audio_file_path):
        print(f"エラー: ファイルが見つかりません: {audio_file_path}")
        return
    
    print(f"テストファイル: {audio_file_path}")
    print(f"ファイルサイズ: {os.path.getsize(audio_file_path)} bytes")
    
    # APIエンドポイント
    url = "http://localhost:8000/analyze"
    
    try:
        # ファイルをアップロード
        filename = os.path.basename(audio_file_path)
        with open(audio_file_path, 'rb') as f:
            files = {'audio_file': (filename, f, 'audio/wav')}
            print("APIリクエスト送信中...")

            response = requests.post(url, files=files, timeout=1800)  # 30分のタイムアウト
            
        print(f"レスポンスステータス: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 分析成功!")
            print("分析結果:")
            print(result.get('analysis', 'No analysis found'))
        else:
            print("❌ 分析失敗")
            print(f"エラー: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ タイムアウトエラー: APIの応答に時間がかかりすぎています")
    except requests.exceptions.ConnectionError:
        print("❌ 接続エラー: バックエンドサーバーに接続できません")
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")

if __name__ == "__main__":
    test_analyze_api()
