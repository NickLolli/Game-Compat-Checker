import { useState } from 'react'
import SearchBar from './components/SearchBar.jsx'
import GameResultsList from './components/GameResultsList.jsx'
import VerdictCard from './components/VerdictCard.jsx'
import { searchGame, compareGame } from './api.js'
import './App.css'

export default function App() {
  const [results, setResults] = useState([])
  const [selectedGame, setSelectedGame] = useState(null)
  const [verdict, setVerdict] = useState(null)
  const [isSearching, setIsSearching] = useState(false)
  const [isComparing, setIsComparing] = useState(false)
  const [error, setError] = useState(null)

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
          Checks this PC's real hardware against any Steam game's requirements.
        </p>
      </header>

      <main className="app__main">
        <SearchBar onSearch={handleSearch} isLoading={isSearching} />

        {error && <div className="app__error">{error}</div>}

        <GameResultsList
          results={results}
          selectedAppId={selectedGame?.appid}
          onSelect={(appid) => {
            const game = results.find((r) => r.appid === appid)
            handleSelectGame(appid, game.name)
          }}
        />

        {isComparing && <div className="app__loading">Comparing hardware…</div>}

        {verdict && !isComparing && (
          <VerdictCard gameName={selectedGame.name} result={verdict} />
        )}
      </main>

      <footer className="app__footer">
        Reads hardware from the machine running the backend locally — not this browser.
      </footer>
    </div>
  )
}
