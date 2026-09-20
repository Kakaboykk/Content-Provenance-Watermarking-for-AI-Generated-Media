import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import GenerateFlow from './pages/GenerateFlow';
import ProtectFlow from './pages/ProtectFlow';
import VerifyFlow from './pages/VerifyFlow';
import HistoryView from './pages/HistoryView';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="generate" element={<GenerateFlow />} />
          <Route path="protect" element={<ProtectFlow />} />
          <Route path="verify" element={<VerifyFlow />} />
          <Route path="history" element={<HistoryView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
