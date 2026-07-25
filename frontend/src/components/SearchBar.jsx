import { useState } from 'react'
import './SearchBar.css'

export default function SearchBar({ onSearch, isLoading }) {
  const [value, setValue] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = value.trim()
    if (trimmed) onSearch(trimmed)
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <span className="search-bar__prompt">&gt;</span>
      <input
        className="search-bar__input"
        type="text"
        placeholder="Search a Steam game…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        aria-label="Search for a game"
      />
      <button className="search-bar__submit" type="submit" disabled={isLoading}>
        {isLoading ? 'Checking…' : 'Check'}
      </button>
    </form>
  )
}
