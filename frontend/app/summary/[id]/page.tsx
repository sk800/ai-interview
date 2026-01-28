'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import axios from 'axios'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'
import { InterviewSummary } from '@/types'

export default function SummaryPage() {
  const router = useRouter()
  const params = useParams()
  const interviewId = params.id as string
  const [summary, setSummary] = useState<InterviewSummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = Cookies.get('token')
    if (!token) {
      router.push('/login')
      return
    }

    loadSummary()
  }, [interviewId, router])

  const loadSummary = async () => {
    try {
      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_API_URL}/api/interviews/${interviewId}/summary`,
        {
          headers: {
            Authorization: `Bearer ${Cookies.get('token')}`
          }
        }
      )
      setSummary(response.data)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to load summary')
      router.push('/dashboard')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container" style={{ textAlign: 'center', paddingTop: '4rem' }}>
        <div>Loading summary...</div>
      </div>
    )
  }

  if (!summary) {
    return null
  }

  return (
    <div className="container">
      <h1 style={{ marginBottom: '2rem' }}>Interview Summary</h1>

      {summary.status === 'terminated' && (
        <div className="card" style={{ marginBottom: '2rem', backgroundColor: '#f8d7da', border: '2px solid #dc3545' }}>
          <h2 style={{ marginBottom: '1rem', color: '#721c24' }}>⚠️ Interview Terminated</h2>
          <p style={{ color: '#721c24', marginBottom: '0.5rem', fontWeight: 'bold' }}>
            Termination Reason:
          </p>
          <p style={{ color: '#721c24', marginBottom: '1rem' }}>
            {summary.termination_reason === 'face_violation' && '🔴 Face Detection Violation - Your face did not match the registered photo during the interview.'}
            {summary.termination_reason === 'audio_violation' && '🔴 Audio Verification Violation - Your voice did not match the registered audio sample during the interview.'}
            {summary.termination_reason === 'tab_switch' && '🔴 Tab Switch Violation - You switched to another tab/window during the interview.'}
            {!summary.termination_reason && '🔴 Interview was terminated due to a violation.'}
          </p>
          <p style={{ color: '#721c24', fontSize: '0.9rem' }}>
            Below are the results for the questions answered before termination.
          </p>
        </div>
      )}

      <div className="card" style={{ marginBottom: '2rem' }}>
        <h2 style={{ marginBottom: '1rem' }}>Overall Performance</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
          <div>
            <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>Interview Type</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{summary.interview_type.toUpperCase()}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>Total Questions</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{summary.total_questions}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>Average Score</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: summary.average_score >= 70 ? '#28a745' : summary.average_score >= 50 ? '#ffc107' : '#dc3545' }}>
              {summary.average_score.toFixed(1)}/100
            </div>
          </div>
        </div>

        <div>
          <h3 style={{ marginBottom: '1rem' }}>Summary</h3>
          <div style={{ 
            padding: '1.5rem', 
            backgroundColor: '#f8f9fa', 
            borderRadius: '0.5rem',
            whiteSpace: 'pre-wrap',
            lineHeight: '1.6'
          }}>
            {summary.summary}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginBottom: '2rem' }}>Detailed Feedback</h2>
        {summary.answers.map((item, index) => (
          <div key={index} style={{ 
            marginBottom: '2rem', 
            paddingBottom: '2rem', 
            borderBottom: index < summary.answers.length - 1 ? '1px solid #ddd' : 'none'
          }}>
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>
                Question {index + 1}
              </div>
              <div style={{ fontSize: '1.1rem', fontWeight: '600', marginBottom: '0.5rem' }}>
                {item.question}
              </div>
            </div>
            
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>Your Answer</div>
              <div style={{ 
                padding: '1rem', 
                backgroundColor: '#f8f9fa', 
                borderRadius: '0.5rem',
                whiteSpace: 'pre-wrap'
              }}>
                {item.answer}
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <div style={{ 
                display: 'inline-block',
                padding: '0.5rem 1rem',
                borderRadius: '0.5rem',
                backgroundColor: item.score >= 70 ? '#d4edda' : item.score >= 50 ? '#fff3cd' : '#f8d7da',
                color: item.score >= 70 ? '#155724' : item.score >= 50 ? '#856404' : '#721c24',
                fontWeight: 'bold'
              }}>
                Score: {item.score.toFixed(1)}/100
              </div>
            </div>

            <div>
              <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '0.5rem' }}>Feedback</div>
              <div style={{ 
                padding: '1rem', 
                backgroundColor: '#e7f3ff', 
                borderRadius: '0.5rem',
                whiteSpace: 'pre-wrap',
                lineHeight: '1.6'
              }}>
                {item.feedback}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ textAlign: 'center', marginTop: '2rem' }}>
        <button
          onClick={() => router.push('/dashboard')}
          className="btn btn-primary"
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  )
}

