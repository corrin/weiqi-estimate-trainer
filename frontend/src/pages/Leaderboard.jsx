import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
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
    if (rank === 1) return 'text-amber-400'
    if (rank === 2) return 'text-stone-400'
    if (rank === 3) return 'text-amber-700'
    return 'text-stone-600'
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between p-4 border-b border-stone-800">
        <Link to="/" className="text-amber-400 font-bold tracking-tight">
          Weiqi Estimate Trainer
        </Link>
        <Link to="/play" className="text-xs text-stone-400 hover:text-white transition-colors">
          Play
        </Link>
      </header>

      <main className="flex-1 px-4 py-6 max-w-lg mx-auto w-full">
        <h2 className="text-xl font-bold text-white mb-6 text-center">Leaderboard</h2>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-6 h-6 border-2 border-amber-400 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : entries.length === 0 ? (
          <div className="text-center py-12 text-stone-500 text-sm">
            No entries yet. Be the first to play!
          </div>
        ) : (
          <div className="space-y-2">
            {entries.map((entry, i) => (
              <div
                key={entry.id}
                className="flex items-center gap-3 bg-stone-800/50 border border-stone-800 rounded-xl p-3"
              >
                <div className={`w-8 text-center font-bold text-sm ${getMedal(i + 1)}`}>
                  {i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-white text-sm truncate">
                    {entry.display_name || entry.email}
                  </div>
                  <div className="text-xs text-stone-500">{entry.total_guesses} guesses</div>
                </div>
                <div className="text-right">
                  <div className="text-amber-400 font-mono font-bold">
                    {entry.avg_deviation}
                  </div>
                  <div className="text-xs text-stone-500">avg dev.</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
