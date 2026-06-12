import { useState } from 'react'

export default function ScoreSlider({ onSubmit, loading }) {
  const [score, setScore] = useState(0)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    setSubmitting(true)
    await onSubmit(score)
    setSubmitting(false)
  }

  const formatScore = (val) => {
    const v = parseInt(val)
    if (v === 0) return 'Even'
    return v > 0 ? `B+${v}` : `W+${Math.abs(v)}`
  }

  if (loading) {
    return (
      <div className="w-full max-w-md mx-auto p-6 text-center">
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-kaya-border rounded w-3/4 mx-auto" />
          <div className="h-10 bg-kaya-border rounded w-full" />
          <div className="h-12 bg-kaya-border rounded w-2/3 mx-auto" />
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-md mx-auto p-4 sm:p-6 space-y-5">
      <h2 className="text-lg font-semibold text-center text-kaya-text font-serif">
        What will the final score be?
      </h2>

      <div className="text-center">
        <span className="text-3xl font-bold font-serif text-kaya-gold">
          {formatScore(score)}
        </span>
      </div>

      <div className="space-y-1">
        <div className="flex justify-between text-xs text-kaya-muted px-1">
          <span>W+50+</span>
          <span>Even</span>
          <span>B+50+</span>
        </div>
        <input
          type="range"
          min="-50"
          max="50"
          step="1"
          value={score}
          onChange={(e) => setScore(parseFloat(e.target.value))}
          className="w-full h-3 rounded-full appearance-none cursor-pointer
            bg-[linear-gradient(to_right,rgb(var(--kaya-bg))_0%,rgb(var(--kaya-border))_48%,rgb(var(--kaya-gold))_50%,rgb(var(--kaya-border))_52%,rgb(var(--kaya-wood))_100%)]
            accent-kaya-gold
            [&::-webkit-slider-thumb]:w-7 [&::-webkit-slider-thumb]:h-7
            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg
            [&::-webkit-slider-thumb]:bg-kaya-gold [&::-webkit-slider-thumb]:border-2
            [&::-webkit-slider-thumb]:border-white [&::-webkit-slider-thumb]:appearance-none
            [&::-moz-range-thumb]:w-7 [&::-moz-range-thumb]:h-7
            [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-kaya-gold
            [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-white"
        />
        <div className="flex justify-between text-xs text-kaya-muted px-1">
          <span>White led</span>
          <span>Even</span>
          <span>Black led</span>
        </div>
      </div>

      <button
        onClick={handleSubmit}
        disabled={submitting}
        className="w-full py-3.5 rounded-xl font-semibold text-sm
          bg-gradient-to-r from-kaya-gold to-kaya-gold-light hover:from-kaya-gold-light hover:to-kaya-gold
          text-white transition-all shadow-lg shadow-kaya-gold/25
          disabled:opacity-50 active:scale-[0.98]"
      >
        {submitting ? 'Checking...' : `Guess: ${formatScore(score)}`}
      </button>
    </div>
  )
}
