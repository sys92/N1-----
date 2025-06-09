import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'

export default function FileUpload({ onFileUpload }) {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onFileUpload(acceptedFiles[0])
    }
  }, [onFileUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/mpeg': ['.mp3'],
      'audio/wav': ['.wav'],
      'audio/mp4': ['.m4a'],
    },
    maxFiles: 1,
    maxSize: 1024 * 1024 * 1024, // 1GB
  })

  return (
    <div className="upload-container">
      <div 
        {...getRootProps()} 
        className={`dropzone ${isDragActive ? 'active' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="upload-content">
          <div className="upload-icon">📁</div>
          {isDragActive ? (
            <p>ファイルをここにドロップしてください</p>
          ) : (
            <div>
              <p>音声ファイルをドラッグ&ドロップするか、クリックして選択してください</p>
              <p className="file-info">対応形式: MP3, WAV, M4A (最大1GB)</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
