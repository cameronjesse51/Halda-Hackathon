import { useState, useRef, useEffect } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function ChatScreen({ studentId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const [profile, setProfile] = useState(null)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim() || streaming) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: userMessage }])
    setStreaming(true)

    setMessages(prev => [...prev, { role: 'assistant', text: '' }])

    try {
      const res = await fetch(`${API_URL}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId, message: userMessage })
      })

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        let eventType = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7)
          } else if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6))

            if (eventType === 'text_delta') {
              setMessages(prev => {
                const updated = [...prev]
                const last = updated[updated.length - 1]
                if (last && last.role === 'assistant') {
                  updated[updated.length - 1] = { ...last, text: last.text + data.text }
                }
                return updated
              })
            } else if (eventType === 'profile_update' || eventType === 'done') {
              setProfile(data.updated_profile)
            }
          }
        }
      }
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev]
        const last = updated[updated.length - 1]
        if (last && last.role === 'assistant' && last.text === '') {
          updated[updated.length - 1] = { ...last, text: 'Sorry, something went wrong. Please try again.' }
        }
        return updated
      })
    }

    setStreaming(false)
  }

  return (
    <div className="chat-layout">
      <div className="chat-main">
        <div className="chat-header">
          <span className="chat-header-logo">HALDA</span>
          <span className="chat-header-subtitle">AI College Counselor</span>
        </div>

        <div className="chat-messages">
          {messages.length === 0 && (
            <div className="chat-empty">
              <p>Hey! I'm Halda. Tell me a bit about yourself and I'll help you figure out the college thing.</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`chat-bubble ${msg.role}`}>
              {msg.role === 'assistant' && <span className="bubble-label">Halda</span>}
              <p>{msg.text}{msg.role === 'assistant' && streaming && i === messages.length - 1 ? '▌' : ''}</p>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-bar" onSubmit={sendMessage}>
          <input
            type="text"
            placeholder="Type a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={streaming}
          />
          <button type="submit" disabled={streaming || !input.trim()}>
            {streaming ? <span className="spinner"></span> : 'Send'}
          </button>
        </form>
      </div>

      <div className="chat-sidebar">
        <h3>Student Profile</h3>
        {profile ? (
          <div className="profile-data">
            {profile.contact?.first_name && (
              <div className="profile-field">
                <span className="field-label">Name</span>
                <span className="field-value">{profile.contact.first_name} {profile.contact.last_name}</span>
              </div>
            )}
            {profile.stage && (
              <div className="profile-field">
                <span className="field-label">Stage</span>
                <span className="profile-tag">{profile.stage}</span>
              </div>
            )}
            {profile.academic?.grade && (
              <div className="profile-field">
                <span className="field-label">Grade</span>
                <span className="field-value">{profile.academic.grade}</span>
              </div>
            )}
            {profile.academic?.gpa && (
              <div className="profile-field">
                <span className="field-label">GPA</span>
                <span className="field-value">{profile.academic.gpa}</span>
              </div>
            )}
            {profile.stated?.interests?.length > 0 && (
              <div className="profile-field">
                <span className="field-label">Interests</span>
                <div className="tag-list">
                  {profile.stated.interests.map((t, i) => <span key={i} className="profile-tag">{t}</span>)}
                </div>
              </div>
            )}
            {profile.stated?.career_goals?.length > 0 && (
              <div className="profile-field">
                <span className="field-label">Career Goals</span>
                <div className="tag-list">
                  {profile.stated.career_goals.map((t, i) => <span key={i} className="profile-tag">{t}</span>)}
                </div>
              </div>
            )}
            <div className="profile-section">
              <span className="field-label">Confidence Scores</span>
              {Object.entries(profile.confidence_scores || {}).map(([key, val]) => (
                <div key={key} className="confidence-bar">
                  <span className="bar-label">{key.replace('_', ' ')}</span>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${(val || 0) * 100}%` }}></div>
                  </div>
                  <span className="bar-value">{((val || 0) * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
            {profile.behavioral?.micro_internship_results?.length > 0 && (
              <div className="profile-section">
                <span className="field-label">Micro-Internships</span>
                {profile.behavioral.micro_internship_results.map((intern, i) => (
                  <div key={i} className="internship-card">
                    <span className="profile-tag">{intern.domain?.replace('_', ' ')}</span>
                    <span className="field-value"> Module {intern.current_module}/3 — {intern.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <p className="sidebar-empty">Profile will appear here as you chat...</p>
        )}
      </div>
    </div>
  )
}

function PhoneInput({ phone, setPhone, onSubmit, loading, error }) {
  return (
    <div className="form-container">
      <h1>Welcome to Halda</h1>
      <p className="subtitle">Enter your phone number to get started</p>
      <form onSubmit={onSubmit}>
        <div className="form-group">
          <label htmlFor="phone">Phone Number</label>
          <div className="input-wrapper">
            <input
              type="tel"
              id="phone"
              placeholder="(555) 123-4567"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
            />
            <span className="input-icon">📱</span>
          </div>
          {error && <div className="error-message show">{error}</div>}
        </div>
        <button type="submit" disabled={loading}>
          {loading ? <span className="spinner"></span> : 'Continue'}
        </button>
      </form>
    </div>
  )
}

function VerificationCode({ code, setCode, onSubmit, loading, error, phone }) {
  return (
    <div className="form-container">
      <h1>Verify your number</h1>
      <p className="subtitle">Enter the 6-digit code we sent to {phone}</p>
      <form onSubmit={onSubmit}>
        <div className="form-group">
          <label htmlFor="code">Verification Code</label>
          <div className="input-wrapper">
            <input
              type="text"
              id="code"
              placeholder="000000"
              value={code}
              onChange={(e) => setCode(e.target.value.slice(0, 6))}
              maxLength="6"
              required
            />
            <span className="input-icon">✓</span>
          </div>
          {error && <div className="error-message show">{error}</div>}
        </div>
        <button type="submit" disabled={loading}>
          {loading ? <span className="spinner"></span> : 'Verify'}
        </button>
      </form>
      <p className="hint">Didn't receive a code? <a href="#">Resend</a></p>
    </div>
  )
}

function Success({ phone, onStartChat }) {
  return (
    <div className="form-container success-state">
      <div className="success-icon">✓</div>
      <h1>Phone verified!</h1>
      <p>Your number {phone} is now verified. We'll send you SMS updates and deadline reminders.</p>
      <button onClick={onStartChat}>Start chatting with Halda</button>
    </div>
  )
}

export default function App() {
  const [step, setStep] = useState('phone') // phone, verify, success, chat
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [studentId, setStudentId] = useState('')

  const validatePhone = (phoneStr) => {
    const digitsOnly = phoneStr.replace(/\D/g, '')
    return digitsOnly.length === 10
  }

  const handlePhoneSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!validatePhone(phone)) {
      setError('Please enter a valid 10-digit phone number')
      return
    }

    setLoading(true)
    const apiUrl = import.meta.env.VITE_API_URL
    console.log('Sending to:', `${apiUrl}/api/send-verification`)
    console.log('Phone:', phone)

    try {
      console.log('Fetching...')
      const response = await fetch(`${apiUrl}/api/send-verification`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone })
      })

      console.log('Response status:', response.status)
      const data = await response.json()
      console.log('Response data:', data)

      if (!response.ok) {
        setError(data.error || 'Failed to send verification code')
        setLoading(false)
        return
      }

      localStorage.setItem('studentPhone', phone)
      setLoading(false)
      setStep('verify')
    } catch (err) {
      console.error('Fetch error:', err)
      setError('Network error. Please try again.')
      setLoading(false)
    }
  }

  const handleVerifySubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (code.length !== 6) {
      setError('Please enter a 6-digit code')
      return
    }

    setLoading(true)

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/verify-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, code })
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.error || 'Verification failed')
        setLoading(false)
        return
      }

      setLoading(false)
      setStep('success')
    } catch (err) {
      setError('Network error. Please try again.')
      setLoading(false)
    }
  }

  const startChat = (id) => {
    setStudentId(id || phone.replace(/\D/g, ''))
    setStep('chat')
  }

  if (step === 'chat') {
    return <ChatScreen studentId={studentId} />
  }

  return (
    <div className="container">
      {/* Left: Branding */}
      <div className="branding-side">
        <div className="halda-logo">HALDA</div>
        {/* Dev shortcut — skip auth for testing */}
        <button
          type="button"
          className="dev-skip-btn"
          onClick={() => startChat('test-jordan')}
        >
          Skip to Chat (dev)
        </button>
      </div>

      {/* Right: Auth */}
      <div className="form-side">
        {step === 'phone' && (
          <PhoneInput
            phone={phone}
            setPhone={setPhone}
            onSubmit={handlePhoneSubmit}
            loading={loading}
            error={error}
          />
        )}

        {step === 'verify' && (
          <VerificationCode
            code={code}
            setCode={setCode}
            onSubmit={handleVerifySubmit}
            loading={loading}
            error={error}
            phone={phone}
          />
        )}

        {step === 'success' && <Success phone={phone} onStartChat={() => startChat()} />}
      </div>
    </div>
  )
}
