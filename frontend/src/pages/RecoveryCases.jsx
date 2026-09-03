import { useState, useEffect } from 'react'
import { RefreshCw } from 'lucide-react'
import RecoveryTable from '../components/RecoveryTable'
import { getJSON } from '../api'

export default function RecoveryCases() {
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      setCases(await getJSON('/recovery/cases'))
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Recovery Cases</h2>
          <p className="text-gray-400 mt-1">{cases.length} cases · click any row for the AI decision</p>
        </div>
        <button onClick={load} className="btn-secondary flex items-center gap-2 text-sm">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>
      <RecoveryTable cases={cases} />
    </div>
  )
}
