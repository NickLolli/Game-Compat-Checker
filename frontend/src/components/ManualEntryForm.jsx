import { useState } from 'react'
import './ManualEntryForm.css'

const EMPTY_TIER = { cpu: '', gpu: '', ram_gb: '' }

function toPayloadTier(tier) {
  const hasAnything = tier.cpu.trim() || tier.gpu.trim() || tier.ram_gb.trim()
  if (!hasAnything) return null
  return {
    cpu: tier.cpu.trim() || null,
    gpu: tier.gpu.trim() || null,
    ram_gb: tier.ram_gb.trim() ? parseFloat(tier.ram_gb) : null,
  }
}

export default function ManualEntryForm({ onSubmit, isLoading }) {
  const [gameName, setGameName] = useState('')
  const [minimum, setMinimum] = useState(EMPTY_TIER)
  const [recommended, setRecommended] = useState(EMPTY_TIER)

  function handleSubmit(e) {
    e.preventDefault()
    if (!gameName.trim()) return

    const minPayload = toPayloadTier(minimum)
    const recPayload = toPayloadTier(recommended)
    if (!minPayload) return // need at least some minimum data to compare against

    onSubmit(gameName.trim(), minPayload, recPayload)
  }

  return (
    <form className="manual-form" onSubmit={handleSubmit}>
      <div className="manual-form__field">
        <label htmlFor="game-name">Game name</label>
        <input
          id="game-name"
          type="text"
          placeholder="e.g. a game from Epic, GOG, or itch.io"
          value={gameName}
          onChange={(e) => setGameName(e.target.value)}
        />
      </div>

      <div className="manual-form__tiers">
        <TierFields title="Minimum" tier={minimum} onChange={setMinimum} />
        <TierFields title="Recommended (optional)" tier={recommended} onChange={setRecommended} />
      </div>

      <button className="manual-form__submit" type="submit" disabled={isLoading || !gameName.trim()}>
        {isLoading ? 'Checking…' : 'Check compatibility'}
      </button>
    </form>
  )
}

function TierFields({ title, tier, onChange }) {
  function update(field, value) {
    onChange({ ...tier, [field]: value })
  }

  return (
    <div className="manual-form__tier">
      <div className="manual-form__tier-title">{title}</div>
      <input
        type="text"
        placeholder="CPU (e.g. Intel Core i5-8400)"
        value={tier.cpu}
        onChange={(e) => update('cpu', e.target.value)}
      />
      <input
        type="text"
        placeholder="GPU (e.g. NVIDIA GTX 1060)"
        value={tier.gpu}
        onChange={(e) => update('gpu', e.target.value)}
      />
      <input
        type="number"
        placeholder="RAM (GB)"
        min="0"
        step="0.5"
        value={tier.ram_gb}
        onChange={(e) => update('ram_gb', e.target.value)}
      />
    </div>
  )
}