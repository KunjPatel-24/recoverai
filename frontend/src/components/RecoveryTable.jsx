import { useNavigate } from 'react-router-dom'
import { inr } from '../api'

function statusBadge(status) {
  if (status === 'SUCCESS') return 'badge-success'
  if (status === 'REJECTED' || status === 'FAILED') return 'badge-danger'
  if (status === 'ESCALATED') return 'badge-warning'
  return 'badge-warning'
}

function priorityTone(p) {
  if (p === 'HIGH' || p === 'CRITICAL') return 'text-danger-400'
  if (p === 'MEDIUM') return 'text-warning-400'
  return 'text-gray-400'
}

export default function RecoveryTable({ cases = [] }) {
  const navigate = useNavigate()
  return (
    <div className="card overflow-hidden p-0">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-gray-400 text-left">
              <th className="px-5 py-3 font-medium">Case</th>
              <th className="px-5 py-3 font-medium">Txn</th>
              <th className="px-5 py-3 font-medium text-right">Amount</th>
              <th className="px-5 py-3 font-medium">Category</th>
              <th className="px-5 py-3 font-medium">Priority</th>
              <th className="px-5 py-3 font-medium">Strategy</th>
              <th className="px-5 py-3 font-medium text-right">Recovered</th>
              <th className="px-5 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {cases.map((c) => (
              <tr
                key={c.id}
                onClick={() => navigate(`/cases/${c.id}`)}
                className="hover:bg-gray-800/40 transition-colors cursor-pointer"
              >
                <td className="px-5 py-3 font-mono text-gray-200">{c.id}</td>
                <td className="px-5 py-3 font-mono text-gray-500">{c.transaction_id}</td>
                <td className="px-5 py-3 text-right text-gray-200">{inr(c.amount_at_risk)}</td>
                <td className="px-5 py-3 text-gray-400">{(c.category || '').replace(/_/g, ' ')}</td>
                <td className={`px-5 py-3 font-medium ${priorityTone(c.priority)}`}>{c.priority}</td>
                <td className="px-5 py-3 text-gray-400">{(c.selected_strategy || '—').replace(/_/g, ' ')}</td>
                <td className="px-5 py-3 text-right text-brand-400">
                  {c.actual_recovered ? inr(c.actual_recovered) : '—'}
                </td>
                <td className="px-5 py-3">
                  <span className={`badge ${statusBadge(c.status)}`}>{c.status}</span>
                </td>
              </tr>
            ))}
            {cases.length === 0 && (
              <tr>
                <td colSpan={8} className="px-5 py-10 text-center text-gray-500">
                  No cases yet. Run recovery from the Command Center.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
