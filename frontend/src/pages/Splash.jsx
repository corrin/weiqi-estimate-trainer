import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import ThemeToggle from '../components/ThemeToggle'
import GoogleSignIn from '../components/GoogleSignIn'

export default function Splash() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [showPrivacy, setShowPrivacy] = useState(false)

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
            <span className="text-kaya-text">How well can you</span>{' '}
            <span className="text-kaya-gold">estimate</span>
            <span className="text-kaya-text">?</span>
          </h1>
          <p className="text-kaya-muted text-base sm:text-lg leading-relaxed">
            Look at a Go board, guess the score difference. Train your positional
            judgment against real professional games analyzed by KataGo.
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
                <button
                  onClick={() => navigate('/leaderboard')}
                  className="px-4 py-2 rounded-lg text-xs text-kaya-muted hover:text-kaya-text hover:bg-kaya-border/50 transition-all"
                >
                  Leaderboard
                </button>
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
            <div className="text-2xl font-bold text-kaya-gold font-serif">34k+</div>
            <div className="text-xs text-kaya-muted mt-1">Pro games analyzed</div>
          </div>
          <div className="bg-kaya-surface border border-kaya-border rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-kaya-gold font-serif">KataGo</div>
            <div className="text-xs text-kaya-muted mt-1">Score evaluation</div>
          </div>
          <div className="bg-kaya-surface border border-kaya-border rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-kaya-gold font-serif">Free</div>
            <div className="text-xs text-kaya-muted mt-1">No ads, no cost</div>
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
              Weiqi Estimate Trainer uses Google Sign-In for authentication. We receive only your email
              address and name from Google. We store your email, guess history, and accuracy stats.
              We don&apos;t share your data with anyone. We don&apos;t use tracking or analytics.
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
