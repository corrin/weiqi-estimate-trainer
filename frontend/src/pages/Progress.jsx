import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
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
        <header className="flex items-center justify-between p-4 border-b border-stone-800">
          <Link to="/" className="text-amber-400 font-bold tracking-tight">Weiqi Estimate Trainer</Link>
          <Link to="/play" className="text-xs text-stone-400 hover:text-white transition-colors">Play</Link>
        </header>
        <main className="flex-1 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
        </main>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="min-h-screen flex flex-col">
        <header className="flex items-center justify-between p-4 border-b border-stone-800">
          <Link to="/" className="text-amber-400 font-bold tracking-tight">Weiqi Estimate Trainer</Link>
          <Link to="/play" className="text-xs text-stone-400 hover:text-white transition-colors">Play</Link>
        </header>
        <main className="flex-1 flex items-center justify-center text-stone-500 text-sm">
          Failed to load stats
        </main>
      </div>
    )
  }

  const getRating = (dev) => {
    if (dev <= 5) return { label: 'Excellent!', color: 'text-emerald-400' }
    if (dev <= 15) return { label: 'Close', color: 'text-amber-400' }
    if (dev <= 30) return { label: 'Not bad', color: 'text-orange-400' }
    return { label: 'Way off', color: 'text-red-400' }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between p-4 border-b border-stone-800">
        <Link to="/" className="text-amber-400 font-bold tracking-tight">Weiqi Estimate Trainer</Link>
        <Link to="/play" className="text-xs text-stone-400 hover:text-white transition-colors">Play</Link>
      </header>

      <main className="flex-1 px-4 py-6 max-w-lg mx-auto w-full space-y-6">
        <h2 className="text-xl font-bold text-white text-center">My Progress</h2>

        <div className="grid grid-cols-3 gap-3">
          <div className="bg-stone-800/50 border border-stone-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-white">{stats.total_guesses}</div>
            <div className="text-xs text-stone-500 mt-1">Guesses</div>
          </div>
          <div className="bg-stone-800/50 border border-stone-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-amber-400">{stats.avg_deviation}</div>
            <div className="text-xs text-stone-500 mt-1">Avg dev.</div>
          </div>
          <div className="bg-stone-800/50 border border-stone-800 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-emerald-400">{stats.best_deviation}</div>
            <div className="text-xs text-stone-500 mt-1">Best</div>
          </div>
        </div>

        <div>
          <h3 className="text-sm font-semibold text-stone-300 mb-3">Recent guesses</h3>
          {stats.recent?.length === 0 ? (
            <p className="text-sm text-stone-500 text-center py-4">No guesses yet.</p>
          ) : (
            <div className="space-y-2">
              {stats.recent?.map((guess, i) => {
                const rating = getRating(guess.deviation)
                return (
                  <div
                    key={i}
                    className="flex items-center gap-3 bg-stone-800/30 border border-stone-800 rounded-xl p-3"
                  >
                    <div className={`text-sm font-bold w-20 ${rating.color}`}>
                      {rating.label}
                    </div>
                    <div className="flex-1 text-xs text-stone-500">
                      <span className="text-stone-300">Guess: {guess.guessed_score >= 0 ? '+' : ''}{guess.guessed_score}</span>
                      <span className="mx-2">|</span>
                      <span className="text-stone-300">Actual: {guess.actual_score >= 0 ? '+' : ''}{guess.actual_score}</span>
                    </div>
                    <div className="text-xs text-stone-500 font-mono">
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
