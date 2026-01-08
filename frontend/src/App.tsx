import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import SkillMapper from './pages/SkillMapper';
import Jobs from './pages/Jobs';
import JobDetail from './pages/JobDetail';
import Chat from './pages/Chat';
import Compare from './pages/Compare';
import CareerPath from './pages/CareerPath';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="skill-mapper" element={<SkillMapper />} />
          <Route path="jobs" element={<Jobs />} />
          <Route path="jobs/:onetCode" element={<JobDetail />} />
          <Route path="chat" element={<Chat />} />
          <Route path="compare" element={<Compare />} />
          <Route path="career-path" element={<CareerPath />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
