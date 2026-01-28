export interface User {
  id: number
  email: string
  full_name: string
}

export interface Question {
  question_id: number
  question: string
  type: string
  time_limit: number
  question_number: number
  total_questions: number
  answer_mode?: 'speaking' | 'writing'
}

export interface Answer {
  answer_id: number
  score: number
  feedback: string
  next_question_available: boolean
}

export interface InterviewSummary {
  interview_id: number
  interview_type: string
  status?: string
  termination_reason?: string  // face_violation, audio_violation, tab_switch
  total_questions: number
  average_score: number
  total_score: number
  summary: string
  answers: Array<{
    question: string
    answer: string
    score: number
    feedback: string
  }>
}

export interface VerificationResult {
  verified: boolean
  alert: boolean
  alert_count?: number
  terminated?: boolean
  message?: string
}

