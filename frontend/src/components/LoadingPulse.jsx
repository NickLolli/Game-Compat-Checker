import './LoadingPulse.css'

export default function LoadingPulse({ label }) {
  return (
    <div className="loading-pulse">
      <span className="loading-pulse__dot" />
      <span className="loading-pulse__dot" />
      <span className="loading-pulse__dot" />
      <span className="loading-pulse__label">{label}</span>
    </div>
  )
}