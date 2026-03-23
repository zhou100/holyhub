import { Link } from 'react-router-dom'

function gradient(id) {
  const hue = (id * 37) % 360
  return `linear-gradient(135deg, hsl(${hue},60%,45%), hsl(${(hue + 40) % 360},50%,35%))`
}

function Stars({ rating }) {
  if (rating == null) return <span className="stars">—</span>
  const full = Math.round(rating)
  return <span className="stars">{'★'.repeat(full)}{'☆'.repeat(5 - full)}</span>
}

function haversine(lat1, lon1, lat2, lon2) {
  const R = 3958.8
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

function Distance({ church, userLat, userLon }) {
  if (userLat == null || !church.latitude || !church.longitude) return null
  const miles = haversine(userLat, userLon, church.latitude, church.longitude)
  const label = miles < 0.1 ? 'nearby'
    : miles < 10 ? `${miles.toFixed(1)} mi`
    : `${Math.round(miles)} mi`
  return <span className="card-distance">📍 {label}</span>
}

export default function ChurchCard({ church, userLat, userLon }) {
  return (
    <Link to={`/church/${church.id}`} className="church-card">
      <div className="card-photo" style={{ background: gradient(church.id) }}>
        ⛪
      </div>
      <div className="card-body">
        <h3>{church.name}</h3>
        <p className="card-denom">{church.denomination || 'Church'}</p>
        <div className="card-meta">
          <Stars rating={church.avg_rating} />
          <span className="review-count">
            {church.avg_rating != null ? church.avg_rating.toFixed(1) : '—'}
            {' '}({church.review_count} {church.review_count === 1 ? 'review' : 'reviews'})
          </span>
          <Distance church={church} userLat={userLat} userLon={userLon} />
        </div>
        <div className="tag-list">
          {church.language && church.language !== 'English' && (
            <span className="tag tag-lang">{church.language}</span>
          )}
          {church.cultural_background && (
            <span className="tag tag-culture">{church.cultural_background}</span>
          )}
          {church.tags?.map(t => <span key={t} className="tag">{t}</span>)}
        </div>
      </div>
    </Link>
  )
}
