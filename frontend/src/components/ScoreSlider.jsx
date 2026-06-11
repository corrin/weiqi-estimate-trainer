import { useState } from 'react'

export default function ScoreSlider({ onSubmit, loading }) {
  const [side, setSide] = useState(null)
  const [points, setPoints] = useState(6.5)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (side === null) return
    setSubmitting(true)
    const sign = side === 'B' ? 1 : -1
    const guessedScore = sign * points
    await onSubmit(guessedScore)
    setSubmitting(false)
  }

  if (loading) {
    return (
      <div className="w-full max-w-md mx-auto p-6 text-center">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-stone-700 rounded w-3/4 mx-auto" />
          <div className="h-10 bg-stone-700 rounded w-full" />
          <div className="h-12 bg-stone-700 rounded w-2/3 mx-auto" />
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-md mx-auto p-4 sm:p-6 space-y-5">
      <h2 className="text-lg font-semibold text-center text-stone-200">
        Who&apos;s leading and by how much?
      </h2>

      <div className="flex gap-3 justify-center">
        <button
          onClick={() => setSide('B')}
          className={`flex-1 py-3 rounded-xl font-medium text-sm transition-all
            ${side === 'B'
              ? 'bg-stone-900 text-white ring-2 ring-amber-400 shadow-lg shadow-amber-400/20'
              : 'bg-stone-800 text-stone-400 hover:bg-stone-700'
            }`}
        >
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 rounded-full bg-stone-900 border border-stone-500" />
            Black leads
          </span>
        </button>
        <button
          onClick={() => setSide('W')}
          className={`flex-1 py-3 rounded-xl font-medium text-sm transition-all
            ${side === 'W'
              ? 'bg-white text-stone-900 ring-2 ring-amber-400 shadow-lg shadow-white/20'
              : 'bg-stone-800 text-stone-400 hover:bg-stone-700'
            }`}
        >
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 rounded-full bg-white border border-stone-300" />
            White leads
          </span>
        </button>
      </div>

      {side && (
        <div className="space-y-4 animate-fade-in">
          <div>
            <div className="flex justify-between text-sm text-stone-400 mb-2">
              <span>by 0.5 pts</span>
              <span className="text-2xl font-bold text-amber-400">{points} pts</span>
              <span>by 50+ pts</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="50"
              step="0.5"
              value={points}
              onChange={(e) => setPoints(parseFloat(e.target.value))}
              className="w-full h-2 bg-stone-700 rounded-lg appearance-none cursor-pointer
                accent-amber-400 [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6
                [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg"
            />
            <div className="flex justify-between text-xs text-stone-500 mt-1">
              <span>0.5</span>
              <span>25</span>
              <span>50+</span>
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full py-3.5 rounded-xl font-semibold text-sm
              bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500
              text-stone-900 transition-all shadow-lg shadow-amber-500/25
              disabled:opacity-50 active:scale-[0.98]"
          >
            {submitting ? 'Checking...' : `Guess: ${side === 'B' ? 'Black' : 'White'} +${points}`}
          </button>
        </div>
      )}
    </div>
  )
}
