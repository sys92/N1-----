import { useState } from 'react'

export default function TranscriptionDisplay({ transcription }) {
  const [copySuccess, setCopySuccess] = useState('')

  const handleCopy = async (text, type) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopySuccess(`${type}をコピーしました！`)
      setTimeout(() => setCopySuccess(''), 2000)
    } catch (err) {
      console.error('コピーに失敗しました:', err)
      setCopySuccess('コピーに失敗しました')
      setTimeout(() => setCopySuccess(''), 2000)
    }
  }

  if (!transcription) {
    return null
  }

  return (
    <div className="transcription-container">
      <h2>📝 文字起こし結果</h2>
      
      {/* コピー成功メッセージ */}
      {copySuccess && (
        <div className="copy-success-message">
          {copySuccess}
        </div>
      )}
      
      {/* 全文文字起こし */}
      <div className="transcription-section">
        <div className="section-header">
          <h3>📄 全文文字起こし</h3>
          <button 
            className="copy-button"
            onClick={() => handleCopy(transcription, '全文文字起こし')}
            title="全文をコピー"
          >
            📋 コピー
          </button>
        </div>
        <div className="transcription-text-container">
          <pre className="transcription-text">
            {transcription}
          </pre>
        </div>
      </div>
    </div>
  )
}
