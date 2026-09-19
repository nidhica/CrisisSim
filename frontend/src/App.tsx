import { BrowserRouter, Routes, Route, useParams } from 'react-router-dom'
import { ScenarioProvider } from './context/ScenarioContext'
import { SimulationProvider } from './context/SimulationContext'
import { ScenarioSelectPage } from './pages/ScenarioSelectPage'
import { DashboardPage } from './pages/DashboardPage'
import { AuthProvider } from './context/AuthContext'
import { LandingPage } from './pages/LandingPage'
import { CitizenDashboardPage } from './pages/CitizenDashboardPage'
import { PersonnelLoginPage } from './pages/PersonnelLoginPage'
import { CreateEmergencyScenarioPage } from './pages/CreateEmergencyScenarioPage'
import { ReportCrisisPage } from './pages/ReportCrisisPage'
import { IncidentDetailPage } from './pages/IncidentDetailPage'
import { PersonnelIncidentDetailPage } from './pages/PersonnelIncidentDetailPage'

function DashboardWrapper() {
  const { id } = useParams<{ id: string }>()
  return (
    <ScenarioProvider>
      <SimulationProvider scenarioId={id!}>
        <DashboardPage />
      </SimulationProvider>
    </ScenarioProvider>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/citizen" element={<CitizenDashboardPage />} />
        <Route path="/citizen/report" element={<ReportCrisisPage />} />
        <Route path="/citizen/reports/:incidentId" element={<IncidentDetailPage />} />
        <Route path="/personnel/login" element={<PersonnelLoginPage />} />
        <Route path="/personnel" element={<ScenarioSelectPage />} />
        <Route path="/personnel/incidents/:incidentId" element={<PersonnelIncidentDetailPage />} />
        <Route path="/personnel/new" element={<CreateEmergencyScenarioPage />} />
        <Route path="/scenario/:id" element={<DashboardWrapper />} />
      </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
