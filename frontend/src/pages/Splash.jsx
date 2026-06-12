import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import ThemeToggle from '../components/ThemeToggle'
import GoogleSignIn from '../components/GoogleSignIn'

export default function Splash() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [showPrivacy, setShowPrivacy] = useState(false)
  const [gameCount, setGameCount] = useState(null)

  useEffect(() => {
    fetch('/api/stats')
      .then(r => r.json())
      .then(d => setGameCount(d.game_count))
      .catch(() => {})
  }, [])

  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between p-4 sm:p-6">
        <div className="text-kaya-gold font-bold text-lg tracking-tight font-serif">
          Weiqi Estimate Trainer
        </div>
        <div className="flex items-center gap-3">
          {user && (
            <>
              <span className="text-sm text-kaya-muted hidden sm:block">{user.email}</span>
              <button
                onClick={logout}
                className="text-xs text-kaya-muted hover:text-kaya-text transition-colors"
              >
                Sign out
              </button>
            </>
          )}
          <ThemeToggle />
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-4 py-12 text-center space-y-8">
        <div className="space-y-4 max-w-lg">
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight font-serif">
            <span className="text-kaya-text">Sharpen your</span>{' '}
            <span className="text-kaya-gold">score sense.</span>
          </h1>
          <p className="text-kaya-muted text-base sm:text-lg leading-relaxed">
            Every strategic choice in Go &mdash; invade or simplify, fight or
            settle &mdash; depends on knowing who&apos;s ahead. Train your
            ability to estimate the score from any position, and build the
            judgment that wins games.
          </p>
        </div>

        <div className="w-full max-w-md">
          {user ? (
            <div className="space-y-4">
              <div className="bg-kaya-surface border border-kaya-border rounded-xl p-5 text-center">
                <div className="text-kaya-muted text-sm mb-1">Signed in as</div>
                <div className="text-kaya-text font-medium">{user.name || user.email}</div>
              </div>
              <button
                onClick={() => navigate('/play')}
                className="w-full py-3.5 rounded-xl font-semibold text-sm
                  bg-gradient-to-r from-kaya-gold to-kaya-gold-light hover:from-kaya-gold-light hover:to-kaya-gold
                  text-white transition-all shadow-lg shadow-kaya-gold/25 active:scale-[0.98]"
              >
                Start estimating
              </button>
              <div className="flex gap-3 justify-center">
                <button
                  onClick={() => navigate('/progress')}
                  className="px-4 py-2 rounded-lg text-xs text-kaya-muted hover:text-kaya-text hover:bg-kaya-border/50 transition-all"
                >
                  My progress
                </button>
                {user.is_admin && (
                  <button
                    onClick={() => navigate('/leaderboard')}
                    className="px-4 py-2 rounded-lg text-xs text-kaya-muted hover:text-kaya-text hover:bg-kaya-border/50 transition-all"
                  >
                    Leaderboard
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              <GoogleSignIn />
              <p className="text-xs text-kaya-muted">
                Free to play. Just sign in with Google.
              </p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 max-w-2xl w-full mt-8">
          <div className="bg-kaya-surface border border-kaya-border rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-kaya-gold font-serif">
              {gameCount !== null ? gameCount.toLocaleString() : '...'}
            </div>
            <div className="text-xs text-kaya-muted mt-1">Real games</div>
          </div>
          <div className="bg-kaya-surface border border-kaya-border rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-kaya-gold font-serif">Instant</div>
            <div className="text-xs text-kaya-muted mt-1">Accuracy feedback</div>
          </div>
          <div className="bg-kaya-surface border border-kaya-border rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-kaya-gold font-serif">Free</div>
            <div className="text-xs text-kaya-muted mt-1">
              &amp;{' '}
              <a
                href="https://github.com/corrin/weiqi-estimate-trainer"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-kaya-gold transition-colors"
              >
                open source
              </a>
            </div>
          </div>
        </div>
      </main>

      <footer className="p-4 text-center">
        <button
          onClick={() => setShowPrivacy(!showPrivacy)}
          className="text-xs text-kaya-muted hover:text-kaya-text transition-colors"
        >
          Privacy
        </button>
      </footer>

      {showPrivacy && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-kaya-bg/80 backdrop-blur-sm" onClick={() => setShowPrivacy(false)} />
          <div className="relative w-full max-w-md bg-kaya-surface border border-kaya-border rounded-2xl p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-kaya-text font-serif">Privacy</h3>
            <p className="text-sm text-kaya-muted leading-relaxed">
              Weiqi Estimate Trainer uses Google Sign-In for authentication. We receive your email
              address and name from Google. Your guesses are stored against your account to track your
              progress and to help us understand which positions are challenging. We don&apos;t share
              your data with third parties. We don&apos;t show ads or sell data.
            </p>
            <button
              onClick={() => setShowPrivacy(false)}
              className="w-full py-2 rounded-lg text-sm text-kaya-muted hover:text-kaya-text hover:bg-kaya-border/50 transition-all"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
