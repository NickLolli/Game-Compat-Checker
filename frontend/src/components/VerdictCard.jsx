import './VerdictCard.css'

const VERDICT_STYLE = {
  'Very good': { tone: 'good', label: 'Very good' },
  'Good': { tone: 'good', label: 'Good' },
  'Playable (lower settings recommended)': { tone: 'warn', label: 'Playable' },
  'Unplayable': { tone: 'bad', label: 'Unplayable' },
  'Unplayable (insufficient RAM)': { tone: 'bad', label: 'Unplayable' },
}

const COMPONENT_LABELS = { cpu: 'CPU', gpu: 'GPU', ram: 'RAM' }

// Bar shows ratio-vs-recommended, capped visually at 1.5x so the
// "recommended" threshold line sits at a consistent, readable spot
// rather than the bar being mostly empty for typical results.
const BAR_CAP = 1.5

function componentStatus(ratioVsMin, ratioVsRec) {
  if (ratioVsMin == null) return { tone: 'unknown', text: 'Unmatched hardware' }
  if (ratioVsMin < 1) return { tone: 'bad', text: 'Below minimum' }
  if (ratioVsRec != null && ratioVsRec >= 1.1) return { tone: 'good', text: 'Exceeds recommended' }
  if (ratioVsRec != null && ratioVsRec >= 1) return { tone: 'good', text: 'Meets recommended' }
  return { tone: 'warn', text: 'Meets minimum only' }
}

function Bar({ ratioVsRec, tone }) {
  const pct = ratioVsRec == null ? 0 : Math.min(ratioVsRec / BAR_CAP, 1) * 100
  const thresholdPct = (1 / BAR_CAP) * 100

  return (
    <div className="verdict-bar">
      <div className="verdict-bar__track">
        <div className={`verdict-bar__fill verdict-bar__fill--${tone}`} style={{ width: `${pct}%` }} />
        <div className="verdict-bar__threshold" style={{ left: `${thresholdPct}%` }} title="Recommended threshold" />
      </div>
    </div>
  )
}

export default function VerdictCard({ gameName, result }) {
  const { verdict, bottleneck, ratios_vs_recommended, ratios_vs_minimum, matched_hardware } = result
  const verdictStyle = VERDICT_STYLE[verdict] || { tone: 'unknown', label: verdict }

  return (
    <div className="verdict-card">
      <div className="verdict-card__header">
        <div>
          <div className="verdict-card__eyebrow">Verdict for</div>
          <h2 className="verdict-card__game">{gameName}</h2>
        </div>
        <div className={`verdict-card__badge verdict-card__badge--${verdictStyle.tone}`}>
          {verdictStyle.label}
        </div>
      </div>

      {bottleneck && (
        <div className="verdict-card__bottleneck">
          Bottleneck: <strong>{COMPONENT_LABELS[bottleneck]}</strong> — upgrading this first will help most.
        </div>
      )}

      <div className="verdict-card__rows">
        {['cpu', 'gpu', 'ram'].map((key) => {
          const ratioMin = ratios_vs_minimum[key]
          const ratioRec = ratios_vs_recommended[key]
          const status = componentStatus(ratioMin, ratioRec)
          const isBottleneck = bottleneck === key

          return (
            <div
              key={key}
              className={
                'verdict-row' +
                (isBottleneck ? ' verdict-row--bottleneck' : '')
              }
            >
              <div className="verdict-row__label">
                {COMPONENT_LABELS[key]}
                {key !== 'ram' && matched_hardware[key] && (
                  <span className="verdict-row__matched">{matched_hardware[key]}</span>
                )}
              </div>
              <Bar ratioVsRec={ratioRec} tone={status.tone} />
              <div className={`verdict-row__status verdict-row__status--${status.tone}`}>
                {status.text}
              </div>
              <div className="verdict-row__ratio">
                {ratioRec != null ? `${ratioRec.toFixed(2)}×` : '—'}
              </div>
            </div>
          )
        })}
      </div>

      <div className="verdict-card__footnote">
        Ratios are relative to this game's <em>recommended</em> requirements. 1.00× means you match it exactly.
      </div>
    </div>
  )
}
