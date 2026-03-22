// DimensionBars renders 6 church-specific dimension bars.
// Uses CSS keyframe animation (fillBar) so bars animate in on mount.
// Pass `animKey` to force re-mount and re-trigger animation after new reviews.

const DIMS = [
  { key: 'worship_energy',       label: 'Worship energy' },
  { key: 'community_warmth',     label: 'Community warmth' },
  { key: 'sermon_depth',         label: 'Sermon depth' },
  { key: 'childrens_programs',   label: "Children's programs" },
  {
    key: 'theological_openness',
    label: 'Theological stance',
    sublabel: '← Traditional  /  Progressive →',
  },
  { key: 'facilities',           label: 'Facilities' },
]

export default function DimensionBars({ dimensions, animKey }) {
  if (!dimensions) return null
  return (
    <div className="dimension-bars" key={animKey}>
      {DIMS.map(({ key, label, sublabel }) => {
        const val = dimensions[key]
        const hasData = val != null
        const pct = hasData ? `${(val / 5) * 100}%` : '100%'
        return (
          <div key={key} className="dim-row">
            <div className="dim-label">
              {label}
              {sublabel && <span className="dim-sublabel">{sublabel}</span>}
            </div>
            <div className="dim-track">
              <div
                className={`dim-fill${hasData ? '' : ' no-data'}`}
                style={{ '--pct': pct }}
                title={hasData ? undefined : 'No ratings yet'}
              />
            </div>
            <div className="dim-value">
              {hasData ? val.toFixed(1) : '—'}
            </div>
          </div>
        )
      })}
    </div>
  )
}
