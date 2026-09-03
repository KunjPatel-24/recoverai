import { inr } from '../api'

const AGENT_DOT = {
  RISK_DETECTOR: 'bg-accent-400 shadow-[0_0_8px_rgba(167,139,250,0.7)]',
  ROOT_CAUSE_ANALYST: 'bg-sky-400 shadow-[0_0_8px_rgba(56,189,248,0.7)]',
  RECOVERY_STRATEGIST: 'bg-brand-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]',
  SAFETY_GUARDIAN: 'bg-warning-400 shadow-[0_0_8px_rgba(251,191,36,0.7)]',
  EXECUTOR: 'bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.7)]',
  OUTCOME_MONITOR: 'bg-brand-500 shadow-[0_0_8px_rgba(16,185,129,0.7)]',
  WEBHOOK_HANDLER: 'bg-pink-400 shadow-[0_0_8px_rgba(244,114,182,0.7)]',
}

export default function AgentTimeline({ logs = [] }) {
  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-200 mb-4 flex items-center gap-2">
        <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
        Live Agent Activity
      </h3>
      <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
        {logs.map((log, i) => (
          <div key={i} className="flex items-start gap-3">
            <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${AGENT_DOT[log.agent] || 'bg-gray-500'}`} />
            <div className="min-w-0">
              <p className="text-sm text-gray-200">
                <span className="text-gray-400">{(log.agent || '').replace(/_/g, ' ')}</span>
                {' · '}
                <span className="font-medium">{(log.action || '').replace(/_/g, ' ')}</span>
                {log.amount ? <span className="text-brand-400"> · {inr(log.amount)}</span> : null}
              </p>
              <p className="text-xs text-gray-500 truncate">{log.details}</p>
            </div>
          </div>
        ))}
        {logs.length === 0 && (
          <p className="text-sm text-gray-500">No activity yet — run recovery to see the agents work.</p>
        )}
      </div>
    </div>
  )
}
