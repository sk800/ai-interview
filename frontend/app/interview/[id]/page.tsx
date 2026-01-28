'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Webcam from 'react-webcam'
import axios from 'axios'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'
import { Question } from '@/types'

export default function InterviewPage() {
  const router = useRouter()
  const params = useParams()
  const interviewId = params.id as string
  const webcamRef = useRef<Webcam>(null)
  const recognitionRef = useRef<any>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)
  const audioRecorderRef = useRef<MediaRecorder | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null)
  const [answer, setAnswer] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [answerMode, setAnswerMode] = useState<'speaking' | 'writing'>('writing')
  const [isListening, setIsListening] = useState(false)
  const [isSpeechComplete, setIsSpeechComplete] = useState(false)
  const [timeLeft, setTimeLeft] = useState(0)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [interviewComplete, setInterviewComplete] = useState(false)
  const [alertCount, setAlertCount] = useState(0)
  const [isTerminated, setIsTerminated] = useState(false)
  const verificationIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const timeIntervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    const token = Cookies.get('token')
    if (!token) {
      router.push('/login')
      return
    }

    // Disable copy-paste
    const handleCopy = (e: ClipboardEvent) => {
      e.preventDefault()
      toast.error('Copy-paste is disabled during interview')
    }
    const handlePaste = (e: ClipboardEvent) => {
      e.preventDefault()
      toast.error('Copy-paste is disabled during interview')
    }
    const handleCut = (e: ClipboardEvent) => {
      e.preventDefault()
      toast.error('Copy-paste is disabled during interview')
    }

    document.addEventListener('copy', handleCopy)
    document.addEventListener('paste', handlePaste)
    document.addEventListener('cut', handleCut)

    // Disable tab switching - terminate immediately on first switch
    const handleVisibilityChange = () => {
      if (document.hidden) {
        toast.error('Tab switch detected! Interview terminated.')
        handleTerminate()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    // Initialize speech recognition if available
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = true
      recognitionRef.current.interimResults = true
      recognitionRef.current.lang = 'en-US'

      recognitionRef.current.onresult = (event: any) => {
        let finalTranscript = ''
        let interimTranscript = ''
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' '
          } else {
            interimTranscript += transcript
          }
        }
        
        // Update final answer with confirmed transcript
        if (finalTranscript) {
          setAnswer(prev => {
            const newAnswer = prev + finalTranscript
            return newAnswer.trim()
          })
          setInterimTranscript('')
        } else {
          // Show interim results in real-time
          setInterimTranscript(interimTranscript)
        }
      }

      recognitionRef.current.onend = () => {
        // When speech recognition ends, mark as complete
        setIsSpeechComplete(true)
        setIsListening(false)
      }

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error)
        if (event.error === 'not-allowed') {
          toast.error('Microphone permission denied')
        }
      }
    }

    // Start verification monitoring
    startVerificationMonitoring()

    // Load first question
    loadQuestion()

    return () => {
      document.removeEventListener('copy', handleCopy)
      document.removeEventListener('paste', handlePaste)
      document.removeEventListener('cut', handleCut)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      stopAllRecording()
    }
  }, [interviewId, router])

  // Stop all recording when interview completes
  useEffect(() => {
    if (interviewComplete || isTerminated) {
      stopAllRecording()
    }
  }, [interviewComplete, isTerminated])

  const startVerificationMonitoring = async () => {
    // Start audio stream for continuous recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      mediaStreamRef.current = stream
    } catch (error) {
      console.error('Error accessing microphone:', error)
    }

    verificationIntervalRef.current = setInterval(async () => {
      await verifyUser()
    }, 5000) // Every 5 seconds
  }

  const verifyUser = async () => {
    try {
      // Capture screenshot
      const imageSrc = webcamRef.current?.getScreenshot()
      if (!imageSrc) return

      // Convert base64 to blob
      const response = await fetch(imageSrc)
      const blob = await response.blob()
      const file = new File([blob], 'snapshot.jpg', { type: 'image/jpeg' })

      // Capture audio clip (5 seconds)
      let audioFile: File | null = null
      if (mediaStreamRef.current) {
        try {
          const audioChunks: BlobPart[] = []
          const audioRecorder = new MediaRecorder(mediaStreamRef.current, {
            mimeType: 'audio/webm'
          })
          
          audioRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
              audioChunks.push(e.data)
            }
          }
          
          const audioPromise = new Promise<void>((resolve) => {
            audioRecorder.onstop = () => {
              const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
              audioFile = new File([audioBlob], 'audio.webm', { type: 'audio/webm' })
              resolve()
            }
          })
          
          audioRecorder.start()
          await new Promise(resolve => setTimeout(resolve, 2000)) // Record 2 seconds
          audioRecorder.stop()
          await audioPromise
        } catch (error) {
          console.error('Error capturing audio:', error)
        }
      }

      const formData = new FormData()
      formData.append('snapshot', file)
      if (audioFile) {
        formData.append('audio_clip', audioFile)
      }

      const result = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/interviews/${interviewId}/verify`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${Cookies.get('token')}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      )

      if (!result.data.verified) {
        setAlertCount(result.data.alert_count || alertCount + 1)
        toast.error(result.data.message || 'Verification failed')
        
        if (result.data.terminated) {
          handleTerminate()
        }
      } else {
        // Verification successful
        if (result.data.alert_reset) {
          // Alert count was reset - show success message
          setAlertCount(0)
          toast.success('Verification successful - Alert count reset!')
        } else {
          // Update alert count if provided (should be 0 if no alerts)
          if (result.data.alert_count !== undefined) {
            setAlertCount(result.data.alert_count)
          }
        }
      }
    } catch (error: any) {
      console.error('Verification error:', error)
    }
  }

  const loadQuestion = async () => {
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/interviews/${interviewId}/question`,
        {
          headers: {
            Authorization: `Bearer ${Cookies.get('token')}`
          }
        }
      )

      if (response.data.completed) {
        // Stop all recording and monitoring immediately
        stopAllRecording()
        setInterviewComplete(true)
        toast.success('Interview completed! Redirecting to evaluation...')
        // Redirect to summary/evaluation page (not samples page)
        setTimeout(() => {
          router.push(`/summary/${interviewId}`)
        }, 1500)
        return
      }

      setCurrentQuestion(response.data)
      setTimeLeft(response.data.time_limit)
      setAnswer('')
      setInterimTranscript('')
      setIsSpeechComplete(false)
      
      // Set random answer mode (speaking or writing)
      const modes: ('speaking' | 'writing')[] = ['speaking', 'writing']
      const randomMode = modes[Math.floor(Math.random() * modes.length)]
      setAnswerMode(randomMode)
      
      // Stop any ongoing speech recognition
      if (recognitionRef.current && isListening) {
        recognitionRef.current.stop()
        setIsListening(false)
        setIsSpeechComplete(false)
      }

      // Start timer
      if (timeIntervalRef.current) {
        clearInterval(timeIntervalRef.current)
      }
      timeIntervalRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            // Auto-submit when timer ends - stop timer and recording first
            if (timeIntervalRef.current) {
              clearInterval(timeIntervalRef.current)
              timeIntervalRef.current = null
            }
            // Stop speech recognition if active before submitting
            if (recognitionRef.current && isListening) {
              recognitionRef.current.stop()
              setIsListening(false)
            }
            handleSubmitAnswer(true)
            return 0
          }
          return prev - 1
        })
      }, 1000)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load question')
    }
  }

  const handleSubmitAnswer = async (autoSubmit = false) => {
    if (!currentQuestion) return

    // Stop speech recognition if active and wait for final results
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
      setIsSpeechComplete(true)
      // Give a moment for final transcription to complete
      await new Promise(resolve => setTimeout(resolve, 500))
    }

    // Submit whatever answer is available (even if empty when timer ends)
    setIsSubmitting(true)
    try {
      const response = await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/interviews/${interviewId}/answer`,
        {
          question_id: currentQuestion.question_id,
          answer_text: answer.trim() || (autoSubmit ? 'No answer provided (time expired)' : 'No answer provided')
        },
        {
          headers: {
            Authorization: `Bearer ${Cookies.get('token')}`
          }
        }
      )

      if (timeIntervalRef.current) {
        clearInterval(timeIntervalRef.current)
      }

      // Check if interview is completed after this answer
      const nextQuestionResponse = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/interviews/${interviewId}/question`,
        {
          headers: {
            Authorization: `Bearer ${Cookies.get('token')}`
          }
        }
      )

      if (nextQuestionResponse.data.completed) {
        // Interview completed - stop all recording and redirect to evaluation page
        stopAllRecording()
        setInterviewComplete(true)
        toast.success('Interview completed! Redirecting to evaluation...')
        // Redirect to summary/evaluation page (not samples page)
        setTimeout(() => {
          router.push(`/summary/${interviewId}`)
        }, 1500)
      } else {
        // Load next question
        await loadQuestion()
      }
    } catch (error: any) {
      // Check if error is due to interview completion
      if (error.response?.status === 400 && error.response?.data?.detail?.includes('completed')) {
        stopAllRecording()
        setInterviewComplete(true)
        toast.success('Interview completed! Redirecting to evaluation...')
        // Redirect to summary/evaluation page (not samples page)
        setTimeout(() => {
          router.push(`/summary/${interviewId}`)
        }, 1500)
      } else {
        toast.error(error.response?.data?.detail || 'Failed to submit answer')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const startListening = () => {
    if (recognitionRef.current && answerMode === 'speaking') {
      try {
        // Reset states for new recording
        setAnswer('')
        setInterimTranscript('')
        setIsSpeechComplete(false)
        
        recognitionRef.current.start()
        setIsListening(true)
        toast.success('Listening... Speak your answer clearly. Your words will appear in real-time.')
      } catch (error) {
        console.error('Error starting speech recognition:', error)
        toast.error('Failed to start speech recognition. Please check microphone permissions.')
      }
    }
  }

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
      setIsSpeechComplete(true)
      // Clear interim transcript when stopping
      setInterimTranscript('')
      toast.success('Stopped listening. Review your answer and submit when ready.')
    }
  }

  const stopAllRecording = () => {
    // Stop speech recognition
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    }
    
    // Stop audio stream
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop())
      mediaStreamRef.current = null
    }
    
    // Stop audio recorder
    if (audioRecorderRef.current && audioRecorderRef.current.state !== 'inactive') {
      audioRecorderRef.current.stop()
      audioRecorderRef.current = null
    }
    
    // Stop timer
    if (timeIntervalRef.current) {
      clearInterval(timeIntervalRef.current)
      timeIntervalRef.current = null
    }
    
    // Stop verification monitoring
    if (verificationIntervalRef.current) {
      clearInterval(verificationIntervalRef.current)
      verificationIntervalRef.current = null
    }
  }

  const handleTerminate = async () => {
    setIsTerminated(true)
    
    // Stop all recording and monitoring
    stopAllRecording()

    // Mark interview as terminated in backend
    try {
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/api/interviews/${interviewId}/terminate`,
        {},
        {
          headers: {
            Authorization: `Bearer ${Cookies.get('token')}`
          }
        }
      )
    } catch (error) {
      console.error('Error terminating interview:', error)
    }

    // Redirect to summary page after a short delay
    setTimeout(() => {
      router.push(`/summary/${interviewId}`)
    }, 1500)
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (isTerminated) {
    return (
      <div className="container" style={{ textAlign: 'center', paddingTop: '4rem' }}>
        <div className="card">
          <h1 style={{ color: '#dc3545', marginBottom: '1rem' }}>Interview Terminated</h1>
          <p>Your interview has been terminated due to a violation (for example, tab switch or identity mismatch).</p>
          <button
            onClick={() => router.push(`/summary/${interviewId}`)}
            className="btn btn-primary"
            style={{ marginTop: '2rem' }}
          >
            View Evaluation
          </button>
        </div>
      </div>
    )
  }

  if (interviewComplete) {
    return (
      <div className="container" style={{ textAlign: 'center', paddingTop: '4rem' }}>
        <div className="card">
          <h1 style={{ marginBottom: '1rem' }}>Interview Completed!</h1>
          <p style={{ marginBottom: '2rem' }}>Redirecting to your evaluation results...</p>
          <div style={{ marginBottom: '1rem' }}>
            <div className="spinner" style={{ 
              border: '4px solid #f3f3f3',
              borderTop: '4px solid #0070f3',
              borderRadius: '50%',
              width: '40px',
              height: '40px',
              animation: 'spin 1s linear infinite',
              margin: '0 auto'
            }}></div>
          </div>
          <button
            onClick={() => router.push(`/summary/${interviewId}`)}
            className="btn btn-primary"
            style={{ marginRight: '1rem' }}
          >
            View Evaluation Now
          </button>
          <button
            onClick={() => router.push('/dashboard')}
            className="btn btn-secondary"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
        <div className="card">
          <h2 style={{ marginBottom: '1rem' }}>Question {currentQuestion?.question_number || 0} of {currentQuestion?.total_questions || 10}</h2>
          <div style={{ 
            fontSize: '1.5rem', 
            fontWeight: 'bold', 
            color: timeLeft < 60 ? '#dc3545' : '#0070f3',
            marginBottom: '1rem'
          }}>
            Time Left: {formatTime(timeLeft)}
          </div>
          {alertCount > 0 && (
            <div style={{ 
              padding: '0.75rem', 
              backgroundColor: '#f8d7da', 
              borderRadius: '0.5rem',
              color: '#721c24',
              marginBottom: '1rem'
            }}>
              ⚠️ Warning: {alertCount}/5 violations detected
              {alertCount >= 4 && (
                <div style={{ marginTop: '0.5rem', fontSize: '0.9rem', fontWeight: 'bold' }}>
                  One more violation will terminate the interview!
                </div>
              )}
            </div>
          )}
          <p style={{ fontSize: '1.1rem', lineHeight: '1.6', marginBottom: '1rem' }}>
            {currentQuestion?.question || 'Loading question...'}
          </p>

          <div style={{ 
            padding: '1rem', 
            backgroundColor: answerMode === 'speaking' ? '#e7f3ff' : '#fff3cd',
            borderRadius: '0.5rem',
            marginBottom: '1.5rem',
            border: `2px solid ${answerMode === 'speaking' ? '#0070f3' : '#ffc107'}`
          }}>
            <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>
              Answer Mode: <span style={{ textTransform: 'uppercase' }}>{answerMode}</span>
            </div>
            {answerMode === 'speaking' ? (
              <p style={{ fontSize: '0.9rem', color: '#666', margin: 0 }}>
                🎤 Please answer by speaking. Click "Start Recording" and speak your answer clearly.
              </p>
            ) : (
              <p style={{ fontSize: '0.9rem', color: '#666', margin: 0 }}>
                ✍️ Please answer by writing. Type your answer in the text box below.
              </p>
            )}
          </div>
          
          {answerMode === 'speaking' ? (
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
                Your Answer (Speaking Mode) - Live Transcription
              </label>
              <textarea
                value={answer + (interimTranscript ? ' ' + interimTranscript : '')}
                readOnly
                className="input"
                rows={8}
                style={{ 
                  resize: 'none',
                  backgroundColor: isListening ? '#e7f3ff' : '#f8f9fa',
                  border: isListening ? '2px solid #28a745' : '1px solid #ddd',
                  color: '#333',
                  cursor: 'default'
                }}
                placeholder={isListening ? "🎤 Listening... Speak your answer and it will appear here in real-time..." : "Click 'Start Speaking' to begin. Your words will appear here as you speak."}
              />
              {isListening && (
                <div style={{ 
                  marginTop: '0.5rem', 
                  color: '#28a745', 
                  fontWeight: 'bold',
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  <span style={{ 
                    display: 'inline-block',
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    backgroundColor: '#28a745',
                    animation: 'pulse 1.5s ease-in-out infinite'
                  }}></span>
                  🎤 Listening... Speak clearly
                </div>
              )}
              {!isListening && answer && (
                <div style={{ 
                  marginTop: '0.5rem', 
                  color: '#666',
                  fontSize: '0.9rem'
                }}>
                  ✓ Transcription complete. You can submit your answer or continue speaking.
                </div>
              )}
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                {!isListening ? (
                  <button
                    onClick={startListening}
                    className="btn btn-primary"
                    style={{ flex: 1 }}
                    disabled={isSubmitting}
                  >
                    🎤 Start Speaking
                  </button>
                ) : (
                  <button
                    onClick={stopListening}
                    className="btn btn-danger"
                    style={{ flex: 1 }}
                    disabled={isSubmitting}
                  >
                    ⏹️ Stop Speaking
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>
                Your Answer (Writing Mode)
              </label>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                onCopy={(e) => {
                  e.preventDefault()
                  toast.error('Copy-paste is disabled during interview')
                }}
                onPaste={(e) => {
                  e.preventDefault()
                  toast.error('Copy-paste is disabled during interview')
                }}
                onCut={(e) => {
                  e.preventDefault()
                  toast.error('Copy-paste is disabled during interview')
                }}
                className="input"
                rows={8}
                style={{ 
                  resize: 'none',
                  userSelect: 'text'
                }}
                placeholder="Type your answer here... (Copy-paste is disabled)"
              />
            </div>
          )}

          <button
            onClick={() => handleSubmitAnswer()}
            className="btn btn-primary"
            style={{ width: '100%' }}
            disabled={
              isSubmitting || 
              (answerMode === 'writing' && !answer.trim()) ||
              (answerMode === 'speaking' && (isListening || (!answer.trim() && !interimTranscript)))
            }
          >
            {isSubmitting ? 'Submitting...' : 
             answerMode === 'speaking' && isListening ? 'Please stop speaking first' :
             answerMode === 'speaking' && !answer.trim() ? 'Please speak your answer first' :
             'Submit Answer'}
          </button>
          
          {timeLeft <= 10 && timeLeft > 0 && (
            <div style={{ 
              marginTop: '1rem',
              padding: '0.75rem',
              backgroundColor: '#fff3cd',
              borderRadius: '0.5rem',
              fontSize: '0.9rem',
              color: '#856404',
              textAlign: 'center'
            }}>
              ⏰ Time running out! Answer will be auto-submitted when timer reaches 0.
            </div>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Video Monitoring</h3>
          <Webcam
            ref={webcamRef}
            audio={false}
            style={{ width: '100%', borderRadius: '0.5rem' }}
            videoConstraints={{
              width: 640,
              height: 480,
              facingMode: 'user'
            }}
            screenshotFormat="image/jpeg"
          />
          <p style={{ marginTop: '1rem', fontSize: '0.9rem', color: '#666' }}>
            Your video is being monitored continuously for identity verification.
          </p>
        </div>
      </div>
    </div>
  )
}

