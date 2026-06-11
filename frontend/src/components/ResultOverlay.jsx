export default function ResultOverlay({ result, onNext }) {
  if (!result) return null

  const ratingColors = {
    'Excellent!': 'text-emerald-400',
    'Close': 'text-amber-400',
    'Not bad': 'text-orange-400',
    'Way off': 'text-red-400',
  }

  const ratingEmoji = {
    'Excellent!': '',
    'Close': '',
    'Not bad': '',
    'Way off': '',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4">
      <div className="absolute inset-0 bg-stone-950/80 backdrop-blur-sm" onClick={onNext} />
      <div className="relative w-full max-w-md bg-stone-900 border border-stone-700 rounded-2xl shadow-2xl p-6 space-y-5 animate-slide-up">
        <div className="text-center space-y-3">
          <div className={`text-5xl font-bold ${ratingColors[result.rating] || 'text-amber-400'}`}>
            {result.rating}
          </div>
          <div className="text-stone-400 text-sm">
            {ratingEmoji[result.rating]} You were off by
          </div>
          <div className="text-4xl font-mono font-bold text-white">
            {result.deviation} <span className="text-xl text-stone-400">pts</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="bg-stone-800 rounded-xl p-3">
            <div className="text-xs text-stone-400 mb-1">Your guess</div>
            <div className="text-lg font-bold text-white">
              {result.guessed_score >= 0 ? '+' : ''}{result.guessed_score}
            </div>
          </div>
          <div className="bg-stone-800 rounded-xl p-3">
            <div className="text-xs text-stone-400 mb-1">Actual score</div>
            <div className="text-lg font-bold text-white">
              {result.actual_score >= 0 ? '+' : ''}{result.actual_score}
            </div>
          </div>
        </div>

        <button
          onClick={onNext}
          className="w-full py-3 rounded-xl font-semibold text-sm
            bg-stone-700 hover:bg-stone-600 text-white transition-all active:scale-[0.98]"
        >
          Next Position
        </button>
      </div>
    </div>
  )
}
