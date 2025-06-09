import formidable from 'formidable'
import fs from 'fs'
import FormData from 'form-data'

export const config = {
  api: {
    bodyParser: false,
  },
}

export default async function handler(req, res) {
  console.log('API analyze called')

  if (req.method !== 'POST') {
    console.log('Method not allowed:', req.method)
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    // Parse the uploaded file
    console.log('Parsing uploaded file...')
    const form = formidable({
      maxFileSize: 200 * 1024 * 1024, // 200MB limit
      keepExtensions: true,
    })

    const [fields, files] = await form.parse(req)
    console.log('Files parsed:', Object.keys(files))
    const audioFile = files.audio_file?.[0]

    if (!audioFile) {
      console.log('No audio file found in request')
      return res.status(400).json({ error: 'No audio file provided' })
    }

    console.log('Audio file details:', {
      filename: audioFile.originalFilename,
      mimetype: audioFile.mimetype,
      size: audioFile.size
    })

    // Validate file type
    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/m4a']
    if (!allowedTypes.includes(audioFile.mimetype)) {
      console.log('Unsupported file type:', audioFile.mimetype)
      return res.status(400).json({ error: 'Unsupported file type' })
    }

    // Forward to Python backend
    console.log('Preparing to forward to backend...')
    const formData = new FormData()
    const fileStream = fs.createReadStream(audioFile.filepath)
    formData.append('audio_file', fileStream, {
      filename: audioFile.originalFilename,
      contentType: audioFile.mimetype,
    })

    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    console.log('Sending request to:', `${backendUrl}/analyze`)

    const response = await fetch(`${backendUrl}/analyze`, {
      method: 'POST',
      body: formData,
      headers: formData.getHeaders(),
    })

    console.log('Backend response status:', response.status)

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Backend error response:', errorText)
      throw new Error(`Backend error: ${response.status} - ${errorText}`)
    }

    const result = await response.json()
    console.log('Backend response received successfully')

    // Clean up temporary file
    fs.unlinkSync(audioFile.filepath)

    res.status(200).json(result)
  } catch (error) {
    console.error('Analysis error:', error)
    console.error('Error stack:', error.stack)
    res.status(500).json({ error: 'Internal server error', details: error.message })
  }
}
