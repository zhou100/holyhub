import { useState, useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import L from 'leaflet'
import ChurchCard from '../components/ChurchCard'

const API = ''
const PAGE = 50

// Fix Leaflet default marker icons (broken by bundlers)
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

function MapBounds({ churches }) {
  const map = useMap()
  useEffect(() => {
    const pts = churches.filter(c => c.latitude && c.longitude)
    if (pts.length === 0) return
    const bounds = L.latLngBounds(pts.map(c => [c.latitude, c.longitude]))
    map.fitBounds(bounds, { padding: [32, 32], maxZoom: 14 })
  }, [churches, map])
  return null
}

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const [city, setCity] = useState(searchParams.get('city') || '')
  const [state, setState] = useState(searchParams.get('state') || '')
  const [churches, setChurches] = useState(null)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [error, setError] = useState(null)
  const [selectedTags, setSelectedTags] = useState([])
  const [view, setView] = useState('list') // 'list' | 'map'
  const [detectedLocation, setDetectedLocation] = useState(null) // { city, state }
  const offsetRef = useRef(0)

  async function fetchPage(cityVal, stateVal, offset, append = false) {
    const url = `${API}/api/churches?city=${encodeURIComponent(cityVal)}&state=${encodeURIComponent(stateVal)}&limit=${PAGE}&offset=${offset}`
    const res = await fetch(url)
    if (!res.ok) throw new Error('Failed to fetch')
    const data = await res.json()
    if (append) {
      setChurches(prev => [...(prev || []), ...data])
    } else {
      setChurches(data)
    }
    setHasMore(data.length === PAGE)
    offsetRef.current = offset + data.length
    return data
  }

  async function handleSearch(e) {
    if (e) e.preventDefault()
    if (!city.trim() || !state.trim()) return
    setSearchParams({ city: city.trim(), state: state.trim() })
    setSelectedTags([])
    setDetectedLocation(null)
    setLoading(true)
    setError(null)
    offsetRef.current = 0
    try {
      await fetchPage(city.trim(), state.trim(), 0)
    } catch (err) {
      setError(`${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  async function handleLoadMore() {
    setLoadingMore(true)
    try {
      await fetchPage(city.trim(), state.trim(), offsetRef.current, true)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingMore(false)
    }
  }

  // On mount: restore from URL params OR auto-detect location from IP
  useEffect(() => {
    const c = searchParams.get('city')
    const s = searchParams.get('state')
    if (c && s) {
      setCity(c)
      setState(s)
      setLoading(true)
      setError(null)
      offsetRef.current = 0
      fetchPage(c, s, 0)
        .then(() => setSelectedTags([]))
        .catch(err => setError(err.message))
        .finally(() => setLoading(false))
    } else {
      // Auto-detect from IP
      setLoading(true)
      fetch('https://ipapi.co/json/')
        .then(r => r.json())
        .then(data => {
          const detCity = data.city
          const detState = data.region_code
          if (detCity && detState && data.country_code === 'US') {
            setCity(detCity)
            setState(detState)
            setDetectedLocation({ city: detCity, state: detState })
            setSearchParams({ city: detCity, state: detState })
            offsetRef.current = 0
            return fetchPage(detCity, detState, 0)
              .then(() => setSelectedTags([]))
          }
        })
        .catch(() => {}) // fail silently — user can search manually
        .finally(() => setLoading(false))
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const availableTags = churches ? [...new Set(churches.flatMap(c => c.tags ?? []))] : []
  const visibleChurches = selectedTags.length === 0
    ? churches
    : churches?.filter(c => selectedTags.every(t => c.tags?.includes(t)))

  const mappable = (visibleChurches || []).filter(c => c.latitude && c.longitude)

  function toggleTag(tag) {
    setSelectedTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag])
  }

  function tryDemo() {
    setCity('Brooklyn')
    setState('NY')
    setTimeout(() => { document.querySelector('form')?.requestSubmit() }, 0)
  }

  return (
    <div className="search-page">
      <header>
        <h1>⛪ HolyHub</h1>
        <p>Find your church — rated on what actually matters.</p>
      </header>

      <form onSubmit={handleSearch}>
        <div className="search-form">
          <input
            value={city} onChange={e => setCity(e.target.value)}
            placeholder="City" aria-label="City"
          />
          <input
            value={state} onChange={e => setState(e.target.value)}
            placeholder="State (e.g. NY)" aria-label="State" style={{ maxWidth: 120 }}
          />
          <button type="submit" className="search-btn" disabled={loading}>
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>
        <div className="demo-hint">
          Try:{' '}
          <button type="button" onClick={tryDemo}>Brooklyn, NY →</button>
        </div>
      </form>

      {detectedLocation && !loading && (
        <p className="location-detected">
          📍 Showing churches near <strong>{detectedLocation.city}, {detectedLocation.state}</strong>
        </p>
      )}

      {error && <p className="error-msg">{error}</p>}
      {loading && <p className="loading">Finding churches…</p>}

      {!loading && churches !== null && (
        <>
          {availableTags.length > 0 && (
            <div className="tag-filter-bar">
              {availableTags.map(tag => (
                <button
                  key={tag} type="button"
                  onClick={() => toggleTag(tag)}
                  className={`tag-filter-pill${selectedTags.includes(tag) ? ' tag-active' : ''}`}
                >
                  {tag}
                </button>
              ))}
              {selectedTags.length > 0 && (
                <button type="button" className="tag-clear" onClick={() => setSelectedTags([])}>
                  Clear filters
                </button>
              )}
            </div>
          )}

          {/* View toggle — only show when we have results */}
          {churches.length > 0 && (
            <div className="view-toggle">
              <button
                type="button"
                className={`view-btn${view === 'list' ? ' view-active' : ''}`}
                onClick={() => setView('list')}
              >
                ☰ List
              </button>
              <button
                type="button"
                className={`view-btn${view === 'map' ? ' view-active' : ''}`}
                onClick={() => setView('map')}
                disabled={mappable.length === 0}
              >
                🗺 Map {mappable.length > 0 && `(${mappable.length})`}
              </button>
            </div>
          )}

          {visibleChurches?.length === 0 ? (
            <div className="empty-state">
              {churches.length === 0
                ? <><p>No churches found in {city}, {state}.</p><p style={{ fontSize: '0.85rem' }}>Try a different city, or be the first to add one!</p></>
                : <p>No churches match the selected filters.</p>
              }
            </div>
          ) : view === 'map' ? (
            <div className="map-container">
              <MapContainer
                center={[39.5, -98.35]}
                zoom={4}
                style={{ height: '500px', width: '100%' }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <MapBounds churches={mappable} />
                {mappable.map(c => (
                  <Marker key={c.id} position={[c.latitude, c.longitude]}>
                    <Popup>
                      <div className="map-popup">
                        <strong>{c.name}</strong>
                        {c.denomination && <span className="popup-denom">{c.denomination}</span>}
                        {c.avg_rating != null && (
                          <span className="popup-rating">★ {c.avg_rating.toFixed(1)}</span>
                        )}
                        <button
                          className="popup-link"
                          onClick={() => navigate(`/church/${c.id}`)}
                        >
                          View details →
                        </button>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
          ) : (
            <>
              <div className="church-grid">
                {visibleChurches?.map(c => <ChurchCard key={c.id} church={c} />)}
              </div>
              {hasMore && selectedTags.length === 0 && (
                <div className="load-more-row">
                  <button
                    type="button"
                    className="load-more-btn"
                    onClick={handleLoadMore}
                    disabled={loadingMore}
                  >
                    {loadingMore ? 'Loading…' : `Load more churches`}
                  </button>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
