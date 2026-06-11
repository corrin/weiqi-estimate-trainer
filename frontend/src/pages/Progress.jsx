import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import ThemeToggle from '../components/ThemeToggle'
import { api } from '../api'

export default function Progress() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api('/me/stats')
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <header className="flex items-center justify-between p-4 border-b border-kaya-border">
          <Link to="/" className="text-kaya-gold font-bold tracking-tight font-serif">Weiqi Estimate Trainer</Link>
          <div className="flex items-center gap-3">
            <Link to="/play" className="text-xs text-kaya-muted hover:text-kaya-text transition-colors">Play</Link>
            <ThemeToggle />
          </div>
        </header>
        <main className="flex-1 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-kaya-gold border-t-transparent rounded-full animate-spin" />
        </main>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="min-h-screen flex flex-col">
        <header className="flex items-center justify-between p-4 border-b border-kaya-border">
          <Link to="/" className="text-kaya-gold font-bold tracking-tight font-serif">Weiqi Estimate Trainer</Link>
          <div className="flex items-center gap-3">
            <Link to="/play" className="text-xs text-kaya-muted hover:text-kaya-text transition-colors">Play</Link>
            <ThemeToggle />
          </div>
        </header>
        <main className="flex-1 flex items-center justify-center text-kaya-muted text-sm">
          Failed to load stats
        </main>
      </div>
    )
  }

  const getRating = (dev) => {
    if (dev <= 3) return { label: 'Excellent!', color: 'text-kaya-success' }
    if (dev <= 10) return { label: 'Close', color: 'text-kaya-gold' }
    if (dev <= 25) return { label: 'Not bad', color: 'text-kaya-wood' }
    return { label: 'Way off', color: 'text-kaya-error' }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between p-4 border-b border-kaya-border">
        <Link to="/" className="text-kaya-gold font-bold tracking-tight font-serif">Weiqi Estimate Trainer</Link>
        <div className="flex items-center gap-3">
          <Link to="/play" className="text-xs text-kaya-muted hover:text-kaya-text transition-colors">Play</Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex-1 px-4 py-6 max-w-lg mx-auto w-full space-y-6">
        <h2 className="text-2xl font-bold text-kaya-text font-serif text-center">My Progress</h2>

        <div className="grid grid-cols-3 gap-3">
          <div className="bg-kaya-surface border border-kaya-border rounded-xl p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-kaya-text font-serif">{stats.total_guesses}</div>
            <div className="text-xs text-kaya-muted mt-1">Guesses</div>
          </div>
          <div className="bg-kaya-surface border border-kaya-border rounded-xl p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-kaya-gold font-serif">{stats.avg_deviation}</div>
            <div className="text-xs text-kaya-muted mt-1">Avg dev.</div>
          </div>
          <div className="bg-kaya-surface border border-kaya-border rounded-xl p-4 text-center shadow-sm">
            <div className="text-2xl font-bold text-kaya-success font-serif">{stats.best_deviation}</div>
            <div className="text-xs text-kaya-muted mt-1">Best</div>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-kaya-text mb-3 font-serif">Recent guesses</h3>
          {stats.recent?.length === 0 ? (
            <p className="text-sm text-kaya-muted text-center py-4">No guesses yet.</p>
          ) : (
            <div className="space-y-2">
              {stats.recent?.map((guess, i) => {
                const rating = getRating(guess.deviation)
                return (
                  <div
                    key={i}
                    className="flex items-center gap-3 bg-kaya-surface border border-kaya-border rounded-xl p-3 shadow-sm"
                  >
                    <div className={`text-sm font-semibold w-20 ${rating.color}`}>
                      {rating.label}
                    </div>
                    <div className="flex-1 text-xs text-kaya-muted">
                      <span className="text-kaya-text">Guess: {guess.guessed_score >= 0 ? '+' : ''}{guess.guessed_score}</span>
                      <span className="mx-2">|</span>
                      <span className="text-kaya-text">Actual: {guess.actual_score >= 0 ? '+' : ''}{guess.actual_score}</span>
                    </div>
                    <div className="text-xs text-kaya-muted font-mono">
                      {guess.deviation.toFixed(1)} pts
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
