export default function ResultOverlay({ result, onNext }) {
  if (!result) return null

  const ratingStyle = {
    'Excellent!': 'text-kaya-success',
    'Close': 'text-kaya-gold',
    'Not bad': 'text-kaya-wood',
    'Way off': 'text-kaya-error',
  }

  const bgTint = {
    'Excellent!': 'bg-kaya-success/5 border-kaya-success/20',
    'Close': 'bg-kaya-gold/5 border-kaya-gold/20',
    'Not bad': 'bg-kaya-wood/5 border-kaya-wood/20',
    'Way off': 'bg-kaya-error/5 border-kaya-error/20',
  }

  const ratingSub = {
    'Excellent!': 'Within 3 pts of the final result',
    'Close': 'Within 10 pts',
    'Not bad': 'Within 25 pts',
    'Way off': 'More than 25 pts off',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4">
      <div className="absolute inset-0 bg-kaya-bg/80 backdrop-blur-sm" onClick={onNext} />
      <div className={`relative w-full max-w-md rounded-2xl shadow-2xl p-6 space-y-5 animate-slide-up border ${bgTint[result.rating] || 'bg-kaya-surface border-kaya-border'}`}>
        <div className="text-center space-y-3">
          <div className={`text-4xl font-bold font-serif ${ratingStyle[result.rating] || 'text-kaya-gold'}`}>
            {result.rating}
          </div>
          <div className="text-kaya-muted text-sm">
            {ratingSub[result.rating] || 'You were off by'}
          </div>
          <div className="text-4xl font-mono font-bold text-kaya-text">
            {result.deviation} <span className="text-xl text-kaya-muted">pts</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="bg-kaya-bg rounded-xl p-3">
            <div className="text-xs text-kaya-muted mb-1">Your guess</div>
            <div className="text-lg font-bold text-kaya-text">
              {result.guessed_score >= 0 ? '+' : ''}{result.guessed_score}
            </div>
          </div>
          <div className="bg-kaya-bg rounded-xl p-3">
            <div className="text-xs text-kaya-muted mb-1">Actual score</div>
            <div className="text-lg font-bold text-kaya-text">
              {result.actual_score >= 0 ? '+' : ''}{result.actual_score}
            </div>
          </div>
        </div>

        <button
          onClick={onNext}
          className="w-full py-3 rounded-xl font-semibold text-sm
            bg-kaya-gold hover:bg-kaya-gold-light text-white transition-all active:scale-[0.98] shadow-md"
        >
          Next Position
        </button>
      </div>
    </div>
  )
}
