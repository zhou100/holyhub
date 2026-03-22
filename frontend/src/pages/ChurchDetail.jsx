import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import DimensionBars from '../components/DimensionBars'
import ReviewForm from '../components/ReviewForm'
import ChurchCard from '../components/ChurchCard'

const API = ''

function gradient(id) {
  const hue = (id * 37) % 360
  return `linear-gradient(135deg, hsl(${hue},60%,45%), hsl(${(hue + 40) % 360},50%,35%))`
}

function Stars({ rating }) {
  if (rating == null) return <span className="stars">—</span>
  const full = Math.round(rating)
  return <span className="stars">{'★'.repeat(full)}{'☆'.repeat(5 - full)}</span>
}

function ReviewCard({ review }) {
  const full = Math.round(review.rating || 0)
  return (
    <div className="review-card">
      <div className="review-stars">{'★'.repeat(full)}{'☆'.repeat(5 - full)}</div>
      {review.comment && <p className="review-comment">{review.comment}</p>}
      <div className="review-date">
        {review.created_at ? new Date(review.created_at).toLocaleDateString() : ''}
      </div>
    </div>
  )
}

export default function ChurchDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [church, setChurch] = useState(null)
  const [reviewData, setReviewData] = useState(null)
  const [churchError, setChurchError] = useState(null)
  const [reviewsError, setReviewsError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [reviewCount, setReviewCount] = useState(0)
  const [similarChurches, setSimilarChurches] = useState(null)
  const [similarError, setSimilarError] = useState(null)

  async function fetchChurch() {
    try {
      const res = await fetch(`${API}/api/churches/${id}`)
      if (!res.ok) throw new Error(res.status === 404 ? 'Church not found' : 'Failed to load')
      setChurch(await res.json())
    } catch (e) {
      setChurchError(e.message)
    }
  }

  async function fetchSimilar() {
    try {
      const res = await fetch(`${API}/api/churches/${id}/similar`)
      if (!res.ok) throw new Error('Failed to load')
      setSimilarChurches(await res.json())
    } catch (e) {
      setSimilarError(e.message)
    }
  }

  async function fetchReviews() {
    try {
      const res = await fetch(`${API}/api/reviews/${id}`)
      if (!res.ok) throw new Error('Failed to load reviews')
      const data = await res.json()
      setReviewData(data)
      setReviewCount(data.reviews.length)
    } catch (e) {
      setReviewsError(e.message)
    }
  }

  useEffect(() => {
    setLoading(true)
    Promise.allSettled([fetchChurch(), fetchReviews(), fetchSimilar()]).then(() => setLoading(false))
  }, [id])

  async function handleReviewSubmitted() {
    await Promise.allSettled([fetchChurch(), fetchReviews()])
  }

  if (loading) return <div className="loading">Loading…</div>

  return (
    <div className="detail-page">
      <button className="back-link" onClick={() => navigate(-1)}>← Back to search</button>

      {churchError
        ? <p className="error-msg">{churchError}</p>
        : church && (
          <>
            <div className="detail-hero" style={{ background: gradient(church.id) }}>⛪</div>
            <div className="detail-header">
              <h1>{church.name}</h1>
              <p className="denom">{church.denomination}</p>
              <p className="address">{church.address}, {church.city}, {church.state}</p>
              {church.service_times && (
                <p className="service-times">🕐 {church.service_times}</p>
              )}
              <div className="meta">
                <Stars rating={church.avg_rating} />
                <span className="avg-rating">
                  {church.avg_rating != null ? church.avg_rating.toFixed(1) : '—'}
                </span>
                <span className="review-count">
                  (<span className="review-count-badge" key={reviewCount}>{reviewCount}</span>
                  {' '}{reviewCount === 1 ? 'review' : 'reviews'})
                </span>
                {church.tags?.map(t => <span key={t} className="tag">{t}</span>)}
              </div>
            </div>
          </>
        )
      }

      <h2 className="section-title">Dimension ratings</h2>
      {reviewsError
        ? <p className="error-msg">{reviewsError}</p>
        : (
          <DimensionBars
            dimensions={reviewData?.dimensions}
            animKey={reviewCount}
          />
        )
      }

      <h2 className="section-title">
        Reviews ({reviewCount})
      </h2>
      {reviewsError
        ? null
        : reviewData?.reviews.length === 0
          ? <p className="empty-state">No reviews yet — be the first!</p>
          : reviewData?.reviews.map(r => <ReviewCard key={r.id} review={r} />)
      }

      {!churchError && church && similarChurches !== null && similarChurches.length > 0 && (
        <>
          <h2 className="section-title">Similar churches</h2>
          {similarError
            ? <p className="error-msg">{similarError}</p>
            : (
              <div className="similar-churches-grid">
                {similarChurches.map(c => <ChurchCard key={c.id} church={c} />)}
              </div>
            )
          }
        </>
      )}

      {!churchError && church && (
        <>
          <h2 className="section-title">Leave a review</h2>
          <ReviewForm churchId={Number(id)} onSubmitted={handleReviewSubmitted} />
        </>
      )}
    </div>
  )
}
