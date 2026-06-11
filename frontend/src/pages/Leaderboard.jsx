import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import { api } from '../api'

export default function Leaderboard() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api('/leaderboard')
      .then(setEntries)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const getMedal = (rank) => {
    if (rank === 1) return 'text-kaya-gold font-bold'
    if (rank === 2) return 'text-kaya-muted font-semibold'
    if (rank === 3) return 'text-kaya-wood'
    return 'text-kaya-muted/50'
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between p-4 border-b border-kaya-border">
        <Link to="/" className="text-kaya-gold font-bold tracking-tight font-serif">
          Weiqi Estimate Trainer
        </Link>
        <div className="flex items-center gap-3">
          <Link to="/play" className="text-xs text-kaya-muted hover:text-kaya-text transition-colors">
            Play
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex-1 px-4 py-6 max-w-lg mx-auto w-full">
        <h2 className="text-2xl font-bold text-kaya-text font-serif text-center mb-6">Leaderboard</h2>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-6 h-6 border-2 border-kaya-gold border-t-transparent rounded-full animate-spin" />
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-12 text-kaya-muted text-sm">
            No entries yet. Be the first to play!
          </div>
        ) : (
          <div className="space-y-2">
            {entries.map((entry, i) => (
              <div
                key={entry.id}
                className="flex items-center gap-3 bg-kaya-surface border border-kaya-border rounded-xl p-3 shadow-sm"
              >
                <div className={`w-8 text-center text-sm ${getMedal(i + 1)}`}>
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-kaya-text text-sm truncate">
                    {entry.display_name || entry.email}
                  </div>
                  <div className="text-xs text-kaya-muted">{entry.total_guesses} guesses</div>
                </div>
                <div className="text-right">
                  <div className="text-kaya-gold font-mono font-bold">
                    {entry.avg_deviation}
                  </div>
                  <div className="text-xs text-kaya-muted">avg dev.</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
