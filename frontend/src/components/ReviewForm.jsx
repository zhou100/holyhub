import { useState } from 'react'
import StarInput from './StarInput'

const API = ''

const DIM_FIELDS = [
  { key: 'worship_energy',       label: 'Worship energy' },
  { key: 'community_warmth',     label: 'Community warmth' },
  { key: 'sermon_depth',         label: 'Sermon depth' },
  { key: 'childrens_programs',   label: "Children's programs" },
  { key: 'theological_openness', label: 'Theological stance' },
  { key: 'facilities',           label: 'Facilities' },
]

export default function ReviewForm({ churchId, onSubmitted }) {
  const [rating, setRating] = useState(null)
  const [comment, setComment] = useState('')
  const [dims, setDims] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(null)

  function setDim(key, val) {
    setDims(prev => ({ ...prev, [key]: val }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    if (!rating) { setError('Please select an overall rating.'); return }
    setSubmitting(true)
    setError(null)
    try {
      const res = await fetch(`${API}/api/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          church_id: churchId,
          rating,
          comment: comment.trim() || null,
          ...Object.fromEntries(Object.entries(dims).filter(([, v]) => v != null)),
        }),
      })
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}))
        throw new Error(detail?.detail || 'Submission failed')
      }
      setSuccess(true)
      setRating(null)
      setComment('')
      setDims({})
      await onSubmitted()
    } catch (e) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (success) {
    return (
      <div className="review-form">
        <p className="submit-success">✓ Review submitted! The dimension bars have been updated.</p>
        <button
          type="button"
          className="submit-btn"
          onClick={() => setSuccess(false)}
          style={{ marginTop: '0.5rem' }}
        >
          Write another review
        </button>
      </div>
    )
  }

  return (
    <form className="review-form" onSubmit={handleSubmit}>
      <h3>Share your experience</h3>

      <div className="form-row">
        <label>Overall rating <span style={{ color: '#e53e3e' }}>*</span></label>
        <StarInput value={rating} onChange={setRating} name="overall" />
      </div>

      <div className="form-row">
        <label>Comment <span className="optional">(optional)</span></label>
        <textarea
          value={comment}
          onChange={e => setComment(e.target.value)}
          placeholder="What was your experience like?"
          maxLength={1000}
        />
      </div>

      <div className="form-row">
        <label>Dimension ratings <span className="optional">(all optional)</span></label>
        <div className="dim-inputs">
          {DIM_FIELDS.map(({ key, label }) => (
            <div key={key}>
              <label style={{ fontSize: '0.78rem', marginBottom: '0.2rem', display: 'block', color: '#666' }}>
                {label}
              </label>
              <StarInput value={dims[key] ?? null} onChange={v => setDim(key, v)} name={label} />
            </div>
          ))}
        </div>
      </div>

      {error && <p className="submit-error">{error}</p>}

      <button type="submit" className="submit-btn" disabled={submitting}>
        {submitting ? 'Submitting…' : 'Submit review'}
      </button>
    </form>
  )
}
