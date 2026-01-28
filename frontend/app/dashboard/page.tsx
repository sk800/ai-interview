'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Webcam from 'react-webcam'
import axios from 'axios'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'

export default function DashboardPage() {
  const router = useRouter()
  const webcamRef = useRef<Webcam>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const [interviewType, setInterviewType] = useState('')
  const [photoBlob, setPhotoBlob] = useState<Blob | null>(null)
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null)
  const [isRecording, setIsRecording] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [samplesUploaded, setSamplesUploaded] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [loading, setLoading] = useState(false)
  const [photoCaptured, setPhotoCaptured] = useState(false)

  useEffect(() => {
    const token = Cookies.get('token')
    if (!token) {
      router.push('/login')
      return
    }
  }, [router])

  const capturePhoto = async () => {
    try {
      const imageSrc = webcamRef.current?.getScreenshot()
      if (!imageSrc) {
        toast.error('Failed to capture photo')
        return
      }

      // Convert base64 to blob
      const response = await fetch(imageSrc)
      const blob = await response.blob()
      setPhotoBlob(blob)
      setPhotoCaptured(true)
      toast.success('Photo captured!')
    } catch (error) {
      toast.error('Error capturing photo')
      console.error(error)
    }
  }

  const startAudioRecording = async () => {
    try {
      // Record audio only
      const audioChunks: BlobPart[] = []
      const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const audioRecorder = new MediaRecorder(audioStream, {
        mimeType: 'audio/webm'
      })
      
      audioRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunks.push(e.data)
        }
      }
      
      audioRecorder.onstop = () => {
        const blob = new Blob(audioChunks, { type: 'audio/webm' })
        setAudioBlob(blob)
      }

      mediaRecorderRef.current = audioRecorder
      audioRecorder.start()
      setIsRecording(true)

      // Record for 5 seconds
      let timeLeft = 5
      setRecordingTime(timeLeft)
      const timer = setInterval(() => {
        timeLeft--
        setRecordingTime(timeLeft)
        if (timeLeft <= 0) {
          clearInterval(timer)
          stopRecording()
        }
      }, 1000)

    } catch (error) {
      toast.error('Error accessing microphone')
      console.error(error)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    setIsRecording(false)
    setRecordingTime(0)
  }

  const handleUploadSamples = async () => {
    if (!photoBlob || !audioBlob) {
      toast.error('Please capture photo and record audio sample first')
      return
    }

    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('photo', photoBlob, 'photo.jpg')
      formData.append('audio', audioBlob, 'audio.webm')

      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/samples/upload`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${Cookies.get('token')}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      toast.success('Samples uploaded successfully!')
      setSamplesUploaded(true)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to upload samples')
    } finally {
      setIsUploading(false)
    }
  }

  const handleStartInterview = async () => {
    if (!interviewType) {
      toast.error('Please select an interview type')
      return
    }

    if (!samplesUploaded) {
      toast.error('Please upload photo and audio samples first')
      return
    }

    setLoading(true)
    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/interviews/start`,
        { interview_type: interviewType },
        {
          headers: {
            Authorization: `Bearer ${Cookies.get('token')}`
          }
        }
      )
      
      router.push(`/interview/${response.data.interview_id}`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to start interview')
    } finally {
      setLoading(false)
    }
  }

  const interviewTypes = ['ai', 'react', 'java', 'python', 'javascript', 'nodejs', 'frontend', 'backend']

  return (
    <div className="container">
      <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Dashboard</h1>
        <button
          onClick={() => {
            Cookies.remove('token')
            router.push('/login')
          }}
          className="btn btn-secondary"
        >
          Logout
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Left Column - Photo/Audio Capture */}
        <div className="card">
          <h2 style={{ marginBottom: '1rem' }}>Upload Photo & Audio Samples</h2>
          <p style={{ marginBottom: '1.5rem', color: '#666', fontSize: '0.9rem' }}>
            Capture a photo and record a 5-second audio sample for identity verification during the interview.
          </p>

          <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
            <Webcam
              ref={webcamRef}
              audio={false}
              screenshotFormat="image/jpeg"
              style={{ width: '100%', maxWidth: '100%', borderRadius: '0.5rem' }}
              videoConstraints={{
                width: 640,
                height: 480,
                facingMode: 'user'
              }}
            />
          </div>

          {/* Photo Capture Section */}
          <div style={{ marginBottom: '1.5rem' }}>
            <button 
              onClick={capturePhoto} 
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={photoCaptured}
            >
              {photoCaptured ? '✓ Photo Captured' : 'Capture Photo'}
            </button>
          </div>

          {/* Audio Recording Section */}
          <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
            {isRecording && (
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#dc3545', marginBottom: '1rem' }}>
                Recording Audio... {recordingTime}s
              </div>
            )}
            {!isRecording && !audioBlob ? (
              <button 
                onClick={startAudioRecording} 
                className="btn btn-primary"
                style={{ width: '100%' }}
                disabled={!photoCaptured}
              >
                Record Audio (5 seconds)
              </button>
            ) : audioBlob ? (
              <div style={{ 
                padding: '0.75rem', 
                backgroundColor: '#d4edda', 
                borderRadius: '0.5rem',
                color: '#155724',
                marginBottom: '1rem'
              }}>
                ✓ Audio recorded successfully
              </div>
            ) : null}
          </div>

          {photoBlob && audioBlob && !samplesUploaded && (
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ 
                padding: '1rem', 
                backgroundColor: '#d4edda', 
                borderRadius: '0.5rem',
                color: '#155724',
                marginBottom: '1rem'
              }}>
                ✓ Photo and audio samples ready
              </div>
              <button
                onClick={handleUploadSamples}
                className="btn btn-primary"
                style={{ width: '100%' }}
                disabled={isUploading}
              >
                {isUploading ? 'Uploading...' : 'Submit Samples'}
              </button>
            </div>
          )}

          {samplesUploaded && (
            <div style={{ 
              padding: '1rem', 
              backgroundColor: '#d1ecf1', 
              borderRadius: '0.5rem',
              color: '#0c5460',
              textAlign: 'center'
            }}>
              ✓ Samples uploaded successfully!
            </div>
          )}
        </div>

        {/* Right Column - Interview Type Selection */}
        <div className="card">
          <h2 style={{ marginBottom: '1rem' }}>Start New Interview</h2>
          
          {!samplesUploaded && (
            <div style={{ 
              padding: '1rem', 
              backgroundColor: '#fff3cd', 
              borderRadius: '0.5rem', 
              marginBottom: '1.5rem',
              color: '#856404'
            }}>
              ⚠️ Please upload photo and audio samples first before starting the interview.
            </div>
          )}

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
              Select Interview Type
            </label>
            <select
              className="input"
              value={interviewType}
              onChange={(e) => setInterviewType(e.target.value)}
              disabled={!samplesUploaded}
            >
              <option value="">Select interview type...</option>
              {interviewTypes.map((type) => (
                <option key={type} value={type}>
                  {type.toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleStartInterview}
            className="btn btn-primary"
            disabled={loading || !interviewType || !samplesUploaded}
            style={{ width: '100%' }}
          >
            {loading ? 'Starting...' : 'Start Interview'}
          </button>

          {samplesUploaded && interviewType && (
            <div style={{ 
              marginTop: '1rem',
              padding: '0.75rem', 
              backgroundColor: '#d4edda', 
              borderRadius: '0.5rem',
              color: '#155724',
              fontSize: '0.9rem'
            }}>
              ✓ Ready to start {interviewType.toUpperCase()} interview
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

