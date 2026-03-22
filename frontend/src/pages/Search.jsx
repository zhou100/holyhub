import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import ChurchCard from '../components/ChurchCard'

const API = ''

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [city, setCity] = useState(searchParams.get('city') || '')
  const [state, setState] = useState(searchParams.get('state') || '')
  const [churches, setChurches] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedTags, setSelectedTags] = useState([])

  async function handleSearch(e) {
    if (e) e.preventDefault()
    if (!city.trim() || !state.trim()) return
    setSearchParams({ city: city.trim(), state: state.trim() })
    setSelectedTags([])
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API}/api/churches?city=${encodeURIComponent(city)}&state=${encodeURIComponent(state)}`)
      if (!res.ok) throw new Error('Failed to fetch')
      setChurches(await res.json())
    } catch (err) {
      setError(`${err.name}: ${err.message} (fetching ${API}/api/churches)`)
    } finally {
      setLoading(false)
    }
  }

  // Restore results when navigating back with URL params
  useEffect(() => {
    const c = searchParams.get('city')
    const s = searchParams.get('state')
    if (c && s && churches === null) {
      setCity(c)
      setState(s)
      setLoading(true)
      setError(null)
      fetch(`${API}/api/churches?city=${encodeURIComponent(c)}&state=${encodeURIComponent(s)}`)
        .then(r => { if (!r.ok) throw new Error('Failed to fetch'); return r.json() })
        .then(data => { setChurches(data); setSelectedTags([]) })
        .catch(err => setError(err.message))
        .finally(() => setLoading(false))
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const availableTags = churches ? [...new Set(churches.flatMap(c => c.tags ?? []))] : []
  const visibleChurches = selectedTags.length === 0
    ? churches
    : churches?.filter(c => selectedTags.every(t => c.tags?.includes(t)))

  function toggleTag(tag) {
    setSelectedTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag])
  }

  function tryDemo() {
    setCity('Brooklyn')
    setState('NY')
    setTimeout(() => {
      const form = document.querySelector('form')
      form?.requestSubmit()
    }, 0)
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

      {error && <p className="error-msg">{error}</p>}

      {loading && <p className="loading">Finding churches…</p>}

      {!loading && churches !== null && availableTags.length > 0 && (
        <div className="tag-filter-bar">
          {availableTags.map(tag => (
            <button
              key={tag}
              type="button"
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

      {!loading && churches !== null && (
        visibleChurches?.length === 0
          ? (
            <div className="empty-state">
              {churches.length === 0
                ? <><p>No churches found in {city}, {state}.</p><p style={{ fontSize: '0.85rem' }}>Try a different city, or be the first to add one!</p></>
                : <p>No churches match the selected filters.</p>
              }
            </div>
          )
          : (
            <div className="church-grid">
              {visibleChurches?.map(c => <ChurchCard key={c.id} church={c} />)}
            </div>
          )
      )}
    </div>
  )
}
