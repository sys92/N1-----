# N1インタビュー分析システム

N1インタビューの音声データを自動で文字起こし・分析するWebアプリケーションです。

## 機能

- 音声ファイル（MP3, WAV, M4A）のアップロード
- OpenAI Whisper APIによる自動文字起こし
- Groq APIによるN1分析（既存認知・新認知の分類）
- 分析結果の表示とコピー機能

## 技術スタック

- **フロントエンド**: Next.js, React
- **バックエンド**: Python FastAPI
- **音声認識**: OpenAI Whisper API
- **AI分析**: Groq API

## セットアップ手順

### 1. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、必要なAPIキーを設定してください。

```bash
cp .env.example .env
```

### 2. バックエンドのセットアップ

```bash
cd backend
pip install -r requirements.txt
python main.py
```

バックエンドは http://localhost:8000 で起動します。

### 3. フロントエンドのセットアップ

```bash
npm install
npm run dev
```

フロントエンドは http://localhost:3000 で起動します。

## 使用方法

1. Webブラウザで http://localhost:3000 にアクセス
2. 音声ファイルをドラッグ&ドロップまたはファイル選択でアップロード
3. 「分析実行」ボタンをクリック
4. 分析結果が表示されたら、「コピー」ボタンで結果をクリップボードにコピー可能

## API仕様

### POST /analyze

音声ファイルを受け取り、文字起こしと分析を実行します。

**リクエスト**:
- `audio_file`: 音声ファイル（multipart/form-data）

**レスポンス**:
```json
{
  "success": true,
  "analysis": "分析結果のMarkdownテキスト",
  "transcription": {
    "segments": [...],
    "full_text": "タイムスタンプ付き文字起こしテキスト"
  }
}
```

## 制限事項

- ファイルサイズ上限: 200MB
- 対応音声形式: MP3, WAV, M4A
- 処理時間: 60分の音声で約15分以内（目標）

## トラブルシューティング

### APIキーエラー
- `.env`ファイルにOpenAI APIキーとGroq APIキーが正しく設定されているか確認してください

### ファイルアップロードエラー
- ファイル形式が対応しているか確認してください（MP3, WAV, M4A）
- ファイルサイズが200MB以下であることを確認してください

### 分析エラー
- バックエンドが正常に起動しているか確認してください
- APIキーの有効性を確認してください
