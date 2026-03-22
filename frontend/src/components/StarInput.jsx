export default function StarInput({ value, onChange, name }) {
  return (
    <div className="star-input" role="group" aria-label={`${name} rating`}>
      {[1, 2, 3, 4, 5].map(n => (
        <button
          key={n}
          type="button"
          aria-label={`${n} star${n > 1 ? 's' : ''}`}
          onClick={() => onChange(value === n ? null : n)}
        >
          {n <= (value || 0) ? '★' : '☆'}
        </button>
      ))}
    </div>
  )
}
