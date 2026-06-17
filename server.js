import express from 'express'
import cors from 'cors'
import twilio from 'twilio'
import dotenv from 'dotenv'

dotenv.config()

const app = express()
app.use(cors())
app.use(express.json())

const client = twilio(
  process.env.TWILIO_ACCOUNT_SID,
  process.env.TWILIO_AUTH_TOKEN
)

// Store verification codes in memory (in production, use a database with TTL)
const verificationCodes = new Map()

// Generate random 6-digit code
function generateCode() {
  return Math.floor(100000 + Math.random() * 900000).toString()
}

// Send verification code via SMS
app.post('/api/send-verification', async (req, res) => {
  try {
    const { phone } = req.body

    if (!phone) {
      return res.status(400).json({ error: 'Phone number required' })
    }

    // Generate code
    const code = generateCode()

    // Store code with 10-minute expiry
    verificationCodes.set(phone, {
      code,
      expiresAt: Date.now() + 10 * 60 * 1000,
      attempts: 0
    })

    // Send SMS
    const message = await client.messages.create({
      from: process.env.TWILIO_PHONE_NUMBER,
      to: phone,
      body: `Your Halda verification code is: ${code}`
    })

    console.log(`SMS sent to ${phone}: SID ${message.sid}`)

    res.json({
      success: true,
      message: 'Verification code sent',
      sid: message.sid
    })
  } catch (error) {
    console.error('SMS send error:', error)
    res.status(500).json({ error: 'Failed to send verification code' })
  }
})

// Verify code
app.post('/api/verify-code', async (req, res) => {
  try {
    const { phone, code } = req.body

    if (!phone || !code) {
      return res.status(400).json({ error: 'Phone and code required' })
    }

    const stored = verificationCodes.get(phone)

    if (!stored) {
      return res.status(400).json({ error: 'No verification code found' })
    }

    if (Date.now() > stored.expiresAt) {
      verificationCodes.delete(phone)
      return res.status(400).json({ error: 'Code expired' })
    }

    if (stored.attempts >= 3) {
      verificationCodes.delete(phone)
      return res.status(400).json({ error: 'Too many attempts' })
    }

    if (stored.code !== code) {
      stored.attempts++
      return res.status(400).json({ error: 'Invalid code' })
    }

    // Code is valid - clean up
    verificationCodes.delete(phone)

    res.json({
      success: true,
      message: 'Phone verified',
      phone
    })
  } catch (error) {
    console.error('Verification error:', error)
    res.status(500).json({ error: 'Verification failed' })
  }
})

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' })
})

const PORT = process.env.PORT || 3001
app.listen(PORT, () => {
  console.log(`🚀 Halda backend running on http://localhost:${PORT}`)
})
