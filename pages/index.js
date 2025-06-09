import { useState } from 'react'
import Head from 'next/head'
import FileUpload from '../components/FileUpload'
import AnalysisResult from '../components/AnalysisResult'
import ProgressBar from '../components/ProgressBar'
import TranscriptionDisplay from '../components/TranscriptionDisplay'

export default function Home() {
  const [uploadedFile, setUploadedFile] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [transcriptionResult, setTranscriptionResult] = useState(null)
  const [error, setError] = useState(null)
  const [sessionId, setSessionId] = useState(null)

  const handleFileUpload = (file) => {
    setUploadedFile(file)
    setAnalysisResult(null)
    setError(null)
  }

  const handleAnalysis = async () => {
    if (!uploadedFile) return

    setIsAnalyzing(true)
    setError(null)
    setAnalysisResult(null)
    setTranscriptionResult(null)

    // セッションIDを生成
    const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    setSessionId(newSessionId)

    try {
      const formData = new FormData()
      formData.append('audio_file', uploadedFile)
      formData.append('session_id', newSessionId)

      // 直接バックエンドに送信
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${backendUrl}/analyze`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`分析に失敗しました: ${response.status} - ${errorText}`)
      }

      const result = await response.json()
      setAnalysisResult(result.analysis)
      setTranscriptionResult(result.full_transcription)
    } catch (err) {
      setError(err.message)
    } finally {
      // プログレスバーが完了を表示してから終了
      setTimeout(() => {
        setIsAnalyzing(false)
      }, 2000)
    }
  }

  const handleProgressComplete = () => {
    // プログレスバーの完了時の処理
    console.log('Progress completed')
  }

  return (
    <div className="container">
      <Head>
        <title>N1インタビュー分析システム</title>
        <meta name="description" content="N1インタビューの音声データを自動で分析するシステム" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="main">
        <h1 className="title">
          N1インタビュー分析システム
        </h1>

        <p className="description">
          音声ファイルをアップロードして、AIによる自動分析を実行します
        </p>

        <div className="upload-section">
          <FileUpload onFileUpload={handleFileUpload} />
          
          {uploadedFile && (
            <div className="file-info">
              <p>アップロード済み: {uploadedFile.name}</p>
              <p>ファイルサイズ: {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          )}

          <button 
            className={`analyze-button ${!uploadedFile || isAnalyzing ? 'disabled' : ''}`}
            onClick={handleAnalysis}
            disabled={!uploadedFile || isAnalyzing}
          >
            {isAnalyzing ? '分析中...' : '分析実行'}
          </button>
        </div>

        {error && (
          <div className="error">
            <p>エラー: {error}</p>
          </div>
        )}

        <ProgressBar
          sessionId={sessionId}
          isAnalyzing={isAnalyzing}
          onComplete={handleProgressComplete}
        />

        {analysisResult && (
          <AnalysisResult result={analysisResult} />
        )}

        {transcriptionResult && (
          <TranscriptionDisplay transcription={transcriptionResult} />
        )}
      </main>
    </div>
  )
}
