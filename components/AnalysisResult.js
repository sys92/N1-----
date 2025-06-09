import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

export default function AnalysisResult({ result }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(result)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="result-container">
      <div className="result-header">
        <h2>📊 N1分析結果</h2>
        <button 
          className={`copy-button ${copied ? 'copied' : ''}`}
          onClick={handleCopy}
        >
          {copied ? 'コピー済み!' : 'コピー'}
        </button>
      </div>
      
      <div className="result-content">
        <ReactMarkdown>{result}</ReactMarkdown>
      </div>
    </div>
  )
}
