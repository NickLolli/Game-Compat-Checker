import './GameResultsList.css'

export default function GameResultsList({ results, onSelect, selectedAppId }) {
  if (!results?.length) return null

  return (
    <div className="results-list">
      <div className="results-list__label">Select a match</div>
      <ul className="results-list__items">
        {results.map((game) => (
          <li key={game.appid}>
            <button
              className={
                'results-list__item' +
                (game.appid === selectedAppId ? ' results-list__item--active' : '')
              }
              onClick={() => onSelect(game.appid)}
            >
              <span className="results-list__name">{game.name}</span>
              <span className="results-list__appid">#{game.appid}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
