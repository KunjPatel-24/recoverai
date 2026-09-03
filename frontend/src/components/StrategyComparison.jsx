import { inr } from '../api'

const LABELS = {
  SMART_RETRY: 'Smart Retry',
  PAYMENT_LINK: 'Payment Link',
  REMINDER: 'Reminder',
  HUMAN_ESCALATION: 'Human Escalation',
}

export default function StrategyComparison({ strategies = [], selected }) {
  const max = Math.max(1, ...strategies.map((s) => s.expected_recovery || 0))
  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">Strategy Comparison</h3>
      <div className="space-y-3">
        {strategies.map((s) => {
          const isSel = s.type === selected
          const pct = Math.round((s.success_probability || 0) * 100)
          const w = Math.max(6, ((s.expected_recovery || 0) / max) * 100)
          return (
            <div key={s.type}>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className={isSel ? 'text-brand-400 font-semibold' : 'text-gray-300'}>
                  {LABELS[s.type] || s.type} {isSel && '← selected'}
                </span>
                <span className="text-gray-500">{pct}%</span>
              </div>
              <div className="h-6 rounded bg-gray-800 overflow-hidden relative">
                <div
                  className={`h-full ${isSel ? 'bg-brand-500' : 'bg-gray-600'}`}
                  style={{ width: `${w}%` }}
                />
                <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[11px] text-gray-200">
                  {inr(s.expected_recovery)}
                </span>
              </div>
            </div>
          )
        })}
      </div>
      <p className="mt-4 text-[11px] text-gray-500">
        Expected recovery = amount at risk × success probability. The agent picks the highest.
      </p>
    </div>
  )
}
