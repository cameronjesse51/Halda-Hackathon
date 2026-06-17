import { useState } from 'react'
import './App.css'

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

function Success({ phone }) {
  return (
    <div className="form-container success-state">
      <div className="success-icon">✓</div>
      <h1>Phone verified!</h1>
      <p>Your number {phone} is now verified. We'll send you SMS updates and deadline reminders.</p>
      <button onClick={() => window.location.reload()}>Start chatting with Halda</button>
    </div>
  )
}

export default function App() {
  const [step, setStep] = useState('phone') // phone, verify, success
  const [phone, setPhone] = useState('')
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

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

  return (
    <div className="container">
      {/* Left: Branding */}
      <div className="branding-side">
        <div className="halda-logo">HALDA</div>
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

        {step === 'success' && <Success phone={phone} />}
      </div>
    </div>
  )
}
