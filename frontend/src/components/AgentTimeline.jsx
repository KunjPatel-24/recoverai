import { inr } from '../api'

const AGENT_DOT = {
  RISK_DETECTOR: 'bg-purple-400',
  ROOT_CAUSE_ANALYST: 'bg-blue-400',
  RECOVERY_STRATEGIST: 'bg-brand-400',
  SAFETY_GUARDIAN: 'bg-warning-400',
  EXECUTOR: 'bg-cyan-400',
  OUTCOME_MONITOR: 'bg-brand-500',
  WEBHOOK_HANDLER: 'bg-pink-400',
}

export default function AgentTimeline({ logs = [] }) {
  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-gray-300 mb-4">Live Agent Activity</h3>
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
