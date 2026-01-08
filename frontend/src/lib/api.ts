import axios from 'axios';
import type {
  Job,
  JobDetail,
  Stats,
  Skill,
  SkillsByType,
  JobBySkill,
  GapAnalysisResult,
  UserSkill,
  CompareResult,
  SearchResult,
  ChatMessage,
} from '../types';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Stats
export async function getStats(): Promise<Stats> {
  const { data } = await api.get('/stats');
  return data.data;
}

// Jobs
export async function getJobs(params: {
  page?: number;
  limit?: number;
  search?: string;
}): Promise<{ jobs: Job[]; pagination: { page: number; limit: number; total: number; pages: number } }> {
  const { data } = await api.get('/jobs', { params });
  return data.data;
}

export async function getJobDetail(onetCode: string): Promise<{ job: Job; competencies: JobDetail['competencies'] }> {
  const { data } = await api.get(`/jobs/${onetCode}`);
  return data.data;
}

// Skills
export async function getSkills(params?: {
  type?: string;
  search?: string;
}): Promise<{ skills_by_type: SkillsByType; all_skills: Skill[] }> {
  const { data } = await api.get('/skills', { params });
  return data.data;
}

export async function getJobsBySkill(skillName: string): Promise<{
  skill: string;
  element_type: string;
  jobs: JobBySkill[];
}> {
  const { data } = await api.get(`/skills/${encodeURIComponent(skillName)}/jobs`);
  return data.data;
}

// Gap Analysis
export async function analyzeGap(
  targetJobCode: string,
  userSkills: UserSkill[]
): Promise<GapAnalysisResult> {
  const { data } = await api.post('/gap-analysis', {
    target_job_code: targetJobCode,
    user_skills: userSkills,
  });
  return data.data;
}

// Compare
export async function compareJobs(jobCodes: string[]): Promise<CompareResult> {
  const { data } = await api.post('/compare', { job_codes: jobCodes });
  return data.data;
}

// Search
export async function search(
  query: string,
  type: 'jobs' | 'skills' | 'all' = 'all',
  limit: number = 10
): Promise<SearchResult> {
  const { data } = await api.get('/search', {
    params: { q: query, type, limit },
  });
  return data.data;
}

// Chat
export async function sendChatMessage(message: string): Promise<{
  response: string;
  analysis?: ChatMessage['analysis'];
  type: string;
}> {
  const { data } = await api.post('/chat', { message });
  return data.data;
}

export default api;
