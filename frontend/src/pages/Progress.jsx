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
      .catch(e => { console.error('Failed to load stats:', e) })
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

  const renderChart = (recent) => {
    if (!recent || recent.length < 3) return null

    const data = [...recent].reverse()
    const W = 280, H = 120, PAD = { top: 16, right: 12, bottom: 20, left: 28 }
    const pw = W - PAD.left - PAD.right
    const ph = H - PAD.top - PAD.bottom

    const maxDev = Math.max(...data.map(d => d.deviation), stats.avg_deviation * 2)
    const y = (d) => PAD.top + ph - (d / maxDev) * ph
    const x = (i) => PAD.left + (i / (data.length - 1)) * pw

    const rolling = []
    for (let i = 0; i < data.length; i++) {
      const start = Math.max(0, i - 4)
      const slice = data.slice(start, i + 1)
      const avg = slice.reduce((s, d) => s + d.deviation, 0) / slice.length
      rolling.push(avg)
    }

    const avgY = y(stats.avg_deviation)

    return (
      <div className="bg-kaya-surface border border-kaya-border rounded-xl p-4 shadow-sm space-y-2">
        <h3 className="text-sm font-semibold text-kaya-text font-serif">Trend</h3>
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto">
          <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={H - PAD.bottom} stroke="rgb(var(--kaya-border))" strokeWidth="1" />
          <line x1={PAD.left} y1={H - PAD.bottom} x2={W - PAD.right} y2={H - PAD.bottom} stroke="rgb(var(--kaya-border))" strokeWidth="1" />
          <line x1={PAD.left} y1={avgY} x2={W - PAD.right} y2={avgY} stroke="rgb(var(--kaya-gold))" strokeWidth="1" strokeDasharray="4,3" opacity="0.5" />
          <text x="4" y={avgY + 4} className="text-[8px]" fill="rgb(var(--kaya-gold))" opacity="0.7">{stats.avg_deviation}</text>
          {data.map((d, i) => (
            <circle key={i} cx={x(i)} cy={y(d.deviation)} r="2.5" fill="rgb(var(--kaya-muted))" opacity="0.4" />
          ))}
          <polyline
            points={rolling.map((v, i) => `${x(i)},${y(v)}`).join(' ')}
            fill="none" stroke="rgb(var(--kaya-gold))" strokeWidth="2" strokeLinejoin="round"
          />
        </svg>
        <div className="flex justify-between text-[10px] text-kaya-muted">
          <span>{data.length} guesses ago</span>
          <span>now</span>
        </div>
      </div>
    )
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

        {renderChart(stats.recent)}

        <div>
          <h3 className="text-sm font-semibold text-kaya-text mb-3 font-serif">Recent guesses</h3>
          {stats.recent?.length === 0 ? (
            <p className="text-sm text-kaya-muted text-center py-4">No guesses yet.</p>
          ) : (
            <div className="space-y-2">
              {stats.recent?.map((guess, i) => {
                const rating = getRating(guess.deviation)
                const hasTurn = guess.turn != null
                const classes = `flex items-center gap-3 bg-kaya-surface border border-kaya-border rounded-xl p-3 shadow-sm${hasTurn ? ' hover:border-kaya-gold/50 transition-colors cursor-pointer' : ''}`
                const content = (
                  <>
                    <div className="flex-1 min-w-0">
                      <div className={`text-sm font-semibold ${rating.color}`}>
                        {rating.label}
                      </div>
                      <div className="text-xs text-kaya-muted mt-0.5">
                        <span className="text-kaya-text">Guess: {guess.guessed_score >= 0 ? '+' : ''}{guess.guessed_score}</span>
                        <span className="mx-2">|</span>
                        <span className="text-kaya-text">Actual: {guess.actual_score >= 0 ? '+' : ''}{guess.actual_score}</span>
                        <span className="mx-2">|</span>
                        <span className="font-mono text-kaya-muted">{guess.deviation.toFixed(1)} pts</span>
                      </div>
                    </div>
                    {hasTurn && (
                      <svg className="w-4 h-4 text-kaya-muted flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                  </>
                )
                if (hasTurn) {
                  return (
                    <Link key={i} to={`/play?game=${encodeURIComponent(guess.filepath)}&turn=${guess.turn}`} className={classes}>
                      {content}
                    </Link>
                  )
                }
                return (
                  <div key={i} className={classes}>
                    {content}
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
