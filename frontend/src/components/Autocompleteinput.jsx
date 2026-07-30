import { useState, useRef, useEffect } from 'react'
import './AutocompleteInput.css'

const MAX_SUGGESTIONS = 8

export default function AutocompleteInput({ value, onChange, options, placeholder }) {
  const [isOpen, setIsOpen] = useState(false)
  const [highlightIndex, setHighlightIndex] = useState(-1)
  const wrapperRef = useRef(null)

  const query = value.trim().toLowerCase()
  const suggestions = query
    ? options.filter((opt) => opt.toLowerCase().includes(query)).slice(0, MAX_SUGGESTIONS)
    : []

  // Close the dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function selectOption(option) {
    onChange(option)
    setIsOpen(false)
    setHighlightIndex(-1)
  }

  function handleKeyDown(e) {
    if (!isOpen || suggestions.length === 0) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlightIndex((i) => Math.min(i + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlightIndex((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' && highlightIndex >= 0) {
      e.preventDefault()
      selectOption(suggestions[highlightIndex])
    } else if (e.key === 'Escape') {
      setIsOpen(false)
    }
  }

  return (
    <div className="autocomplete" ref={wrapperRef}>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => {
          onChange(e.target.value)
          setIsOpen(true)
          setHighlightIndex(-1)
        }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={handleKeyDown}
        autoComplete="off"
      />
      {isOpen && suggestions.length > 0 && (
        <ul className="autocomplete__list">
          {suggestions.map((option, i) => (
            <li key={option}>
              <button
                type="button"
                className={
                  'autocomplete__option' +
                  (i === highlightIndex ? ' autocomplete__option--highlighted' : '')
                }
                onMouseDown={(e) => e.preventDefault()} // keep input focus so click registers before blur
                onClick={() => selectOption(option)}
              >
                {option}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}