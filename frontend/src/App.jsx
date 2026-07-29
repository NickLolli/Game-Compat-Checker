import { useState } from 'react'
import SearchBar from './components/SearchBar.jsx'
import GameResultsList from './components/GameResultsList.jsx'
import VerdictCard from './components/VerdictCard.jsx'
import LoadingPulse from './components/LoadingPulse.jsx'
import ManualEntryForm from './components/ManualEntryForm.jsx'
import { searchGame, compareGame, compareManual } from './api.js'
import './App.css'

export default function App() {
  const [mode, setMode] = useState('steam') // 'steam' | 'manual'
  const [results, setResults] = useState([])
  const [selectedGame, setSelectedGame] = useState(null)
  const [verdict, setVerdict] = useState(null)
  const [verdictGameName, setVerdictGameName] = useState(null)
  const [isSearching, setIsSearching] = useState(false)
  const [isComparing, setIsComparing] = useState(false)
  const [error, setError] = useState(null)

  function switchMode(newMode) {
    if (newMode === mode) return
    setMode(newMode)
    setError(null)
    setVerdict(null)
    setResults([])
    setSelectedGame(null)
  }

  async function handleSearch(query) {
    setError(null)
    setVerdict(null)
    setSelectedGame(null)
    setIsSearching(true)
    try {
      const matches = await searchGame(query)
      setResults(matches)
      // Auto-select the top match so a single-result search feels instant
      if (matches.length === 1) {
        handleSelectGame(matches[0].appid, matches[0].name)
      }
    } catch (err) {
      setError(err.message)
      setResults([])
    } finally {
      setIsSearching(false)
    }
  }

  async function handleSelectGame(appid, name) {
    setError(null)
    setSelectedGame({ appid, name })
    setIsComparing(true)
    setVerdict(null)
    try {
      const result = await compareGame(appid)
      setVerdictGameName(name)
      setVerdict(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsComparing(false)
    }
  }

  async function handleManualSubmit(gameName, minimum, recommended) {
    setError(null)
    setIsComparing(true)
    setVerdict(null)
    try {
      const result = await compareManual(gameName, minimum, recommended)
      setVerdictGameName(gameName)
      setVerdict(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setIsComparing(false)
    }
  }

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__eyebrow">Local hardware diagnostic</div>
        <h1 className="app__title">Can it run?</h1>
        <p className="app__subtitle">
          Checks this PC's real hardware against any game's requirements.
        </p>
      </header>

      <main className="app__main">
        <div className="app__mode-toggle">
          <button
            className={mode === 'steam' ? 'app__mode-btn app__mode-btn--active' : 'app__mode-btn'}
            onClick={() => switchMode('steam')}
          >
            Search Steam
          </button>
          <button
            className={mode === 'manual' ? 'app__mode-btn app__mode-btn--active' : 'app__mode-btn'}
            onClick={() => switchMode('manual')}
          >
            Enter manually
          </button>
        </div>

        {mode === 'steam' ? (
          <SearchBar onSearch={handleSearch} isLoading={isSearching} />
        ) : (
          <ManualEntryForm onSubmit={handleManualSubmit} isLoading={isComparing} />
        )}

        {error && <div className="app__error">{error}</div>}

        {mode === 'steam' && (
          <GameResultsList
            results={results}
            selectedAppId={selectedGame?.appid}
            onSelect={(appid) => {
              const game = results.find((r) => r.appid === appid)
              handleSelectGame(appid, game.name)
            }}
          />
        )}

        {isComparing && <LoadingPulse label="Comparing hardware…" />}

        {verdict && !isComparing && (
          <VerdictCard gameName={verdictGameName} result={verdict} />
        )}
      </main>

      <footer className="app__footer">
        Reads hardware from the machine running the backend locally — not this browser.
      </footer>
    </div>
  )
}