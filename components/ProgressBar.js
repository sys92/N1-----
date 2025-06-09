import { useEffect, useState } from 'react'

export default function ProgressBar({ sessionId, isAnalyzing, onComplete }) {
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState('')
  const [message, setMessage] = useState('')
  const [websocket, setWebsocket] = useState(null)

  useEffect(() => {
    if (isAnalyzing && sessionId) {
      // WebSocket接続を開始
      const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`)
      
      ws.onopen = () => {
        console.log('🔌 WebSocket connected to:', `ws://localhost:8000/ws/${sessionId}`)
        setWebsocket(ws)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('📡 WebSocket received:', data)
          setProgress(data.progress)
          setStage(data.stage)
          setMessage(data.message)

          // 完了時の処理
          if (data.stage === 'completed' && data.progress === 100) {
            setTimeout(() => {
              if (onComplete) onComplete()
            }, 1000)
          }
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error)
        }
      }
      
      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error)
      }

      ws.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason)
        setWebsocket(null)
      }
      
      return () => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close()
        }
      }
    } else {
      // 分析が終了したらWebSocketを閉じる
      if (websocket) {
        websocket.close()
        setWebsocket(null)
      }
      // プログレスをリセット
      setProgress(0)
      setStage('')
      setMessage('')
    }
  }, [isAnalyzing, sessionId])

  if (!isAnalyzing) {
    return null
  }

  const getStageText = (stage) => {
    switch (stage) {
      case 'upload': return 'アップロード'
      case 'validation': return 'ファイル検証'
      case 'loading': return '音声読み込み'
      case 'preparing': return '分割準備'
      case 'segmenting': return '音声分割'
      case 'splitting': return 'セグメント切り出し'
      case 'transcribing': return '音声認識'
      case 'merging': return '結果マージ'
      case 'transcription_complete': return '音声認識完了'
      case 'analysis': return 'AI分析'
      case 'completed': return '完了'
      case 'error': return 'エラー'
      default: return '処理中'
    }
  }

  const getProgressColor = (stage) => {
    switch (stage) {
      case 'error': return '#e74c3c'
      case 'completed': return '#27ae60'
      default: return '#3498db'
    }
  }

  return (
    <div className="progress-container">
      <div className="progress-header">
        <h3>処理状況</h3>
        <span className="progress-percentage">{progress}%</span>
      </div>
      
      <div className="progress-bar-wrapper">
        <div 
          className="progress-bar"
          style={{ 
            width: `${progress}%`,
            backgroundColor: getProgressColor(stage)
          }}
        />
      </div>
      
      <div className="progress-info">
        <div className="stage-text">{getStageText(stage)}</div>
        <div className="message-text">{message}</div>
        {stage === 'transcribing' && progress > 15 && progress < 75 && (
          <div className="progress-detail">
            音声認識処理中... しばらくお待ちください
          </div>
        )}
      </div>
    </div>
  )
}
