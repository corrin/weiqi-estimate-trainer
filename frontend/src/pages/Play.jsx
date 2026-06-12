import { useState, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import ThemeToggle from '../components/ThemeToggle'
import { api } from '../api'
import GoBoard from '../components/GoBoard'
import ScoreSlider from '../components/ScoreSlider'
import ResultOverlay from '../components/ResultOverlay'

export default function Play() {
  const { user, logout } = useAuth()
  const [searchParams] = useSearchParams()
  const [position, setPosition] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  const fetchPosition = useCallback(async (specific = false) => {
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      let url = '/position'
      const g = searchParams.get('game')
      const t = searchParams.get('turn')
      if (specific && g && t) {
        url = `/position?game_id=${g}&turn=${t}`
      }
      const data = await api(url)
      setPosition(data)
      if (!g || !t) {
        window.history.replaceState(null, '', `/play?game=${data.game_id}&turn=${data.turn}`)
      }
    } catch (e) {
      console.error('Failed to load position:', e)
      setError(e.message || 'Failed to load position')
    }
    setLoading(false)
  }, [searchParams])

  useEffect(() => {
    fetchPosition(true)
  }, [fetchPosition])

  const handleGuess = async (guessedScore) => {
    if (!position) return
    try {
      const data = await api('/guess', {
        method: 'POST',
        body: JSON.stringify({
          game_id: position.game_id,
          turn: position.turn,
          guessed_score: guessedScore,
        }),
      })
      setResult(data)
    } catch (e) {
      console.error('Failed to submit guess:', e)
      setError(e.message || 'Failed to submit guess')
    }
  }

  const handleCopyRef = () => {
    const url = `${window.location.origin}/play?game=${position.game_id}&turn=${position.turn}`
    navigator.clipboard.writeText(url)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between p-3 sm:p-4 border-b border-kaya-border">
        <Link to="/" className="text-kaya-gold font-bold tracking-tight font-serif">
          Weiqi Estimate Trainer
        </Link>
        <div className="flex items-center gap-3">
          {user.is_admin && (
            <Link to="/leaderboard" className="text-xs text-kaya-muted hover:text-kaya-text transition-colors">
              Leaderboard
            </Link>
          )}
          <Link to="/progress" className="text-xs text-kaya-muted hover:text-kaya-text transition-colors">
            Progress
          </Link>
          <button onClick={logout} className="text-xs text-kaya-muted hover:text-kaya-text transition-colors">
            Sign out
          </button>
          <ThemeToggle />
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center px-2 sm:px-4 py-4 sm:py-6 max-w-2xl mx-auto w-full">
        {error && (
          <div className="w-full mb-4 p-3 rounded-lg bg-kaya-error/10 border border-kaya-error/30 text-kaya-error text-sm">
            {error}
            <button onClick={fetchPosition} className="ml-3 underline">
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className="flex-1 flex flex-col items-center justify-center space-y-4">
            <div className="w-8 h-8 border-2 border-kaya-gold border-t-transparent rounded-full animate-spin" />
            <p className="text-kaya-muted text-sm">Loading position...</p>
          </div>
        ) : position ? (
          <div className="w-full space-y-4">
            <div className="flex items-center justify-between text-xs text-kaya-muted px-1">
              <button
                onClick={handleCopyRef}
                className="font-mono hover:text-kaya-gold transition-colors"
                title="Copy link to this position"
              >
                #{position.game_id}:{position.turn}
                {copied && <span className="ml-1 text-kaya-success">copied</span>}
              </button>
              <span>{position.next_to_play} to play</span>
              <span>Komi 7.0</span>
            </div>

            <div className="border-4 border-kaya-wood rounded-sm bg-kaya-surface overflow-hidden shadow-xl">
              <GoBoard
                stones={position.stones}
                size={position.board_size}
                lastMove={position.last_move}
              />
            </div>

            <ScoreSlider onSubmit={handleGuess} loading={false} />
          </div>
        ) : null}

        {result && (
          <ResultOverlay result={result} onNext={fetchPosition} />
        )}
      </main>
    </div>
  )
}
