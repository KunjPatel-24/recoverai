import { Routes, Route, NavLink } from 'react-router-dom'
import { LayoutDashboard, ListChecks, ShieldCheck, ScrollText, Activity } from 'lucide-react'

import Dashboard from './pages/Dashboard'
import RecoveryCases from './pages/RecoveryCases'
import DecisionView from './pages/DecisionView'
import Safety from './pages/Safety'
import AuditTrail from './pages/AuditTrail'

const nav = [
  { to: '/', label: 'Command Center', icon: LayoutDashboard, end: true },
  { to: '/cases', label: 'Recovery Cases', icon: ListChecks },
  { to: '/safety', label: 'Policy & Safety', icon: ShieldCheck },
  { to: '/audit', label: 'Audit Trail', icon: ScrollText },
]

export default function App() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 border-r border-gray-800 bg-gray-900/50 p-4 hidden md:flex md:flex-col">
        <div className="flex items-center gap-2 px-2 mb-8">
          <div className="w-9 h-9 rounded-lg bg-brand-600 flex items-center justify-center">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-bold text-white leading-tight">RecoverAI</p>
            <p className="text-[11px] text-gray-500 leading-tight">Revenue Recovery</p>
          </div>
        </div>
        <nav className="space-y-1">
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-brand-950/50 text-brand-300 border border-brand-900'
                    : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                }`
              }
            >
              <n.icon className="w-4 h-4" />
              {n.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto px-2 pt-6 text-[11px] text-gray-600">
          Track 03 · Bounded agent · Offline demo
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 min-w-0 overflow-x-hidden p-6 lg:p-8 max-w-[1400px] mx-auto w-full">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cases" element={<RecoveryCases />} />
          <Route path="/cases/:caseId" element={<DecisionView />} />
          <Route path="/safety" element={<Safety />} />
          <Route path="/audit" element={<AuditTrail />} />
        </Routes>
      </main>
    </div>
  )
}
