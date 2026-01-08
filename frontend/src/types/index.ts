// Job Types
export interface Job {
  onet_soc_code: string;
  title: string;
  description: string;
}

export interface JobDetail extends Job {
  competencies: CompetenciesByType;
}

export interface Competency {
  element_name: string;
  data_value: number;
  scale_name?: string;
}

export interface CompetenciesByType {
  Skill?: Competency[];
  Ability?: Competency[];
  Knowledge?: Competency[];
  Task?: Competency[];
}

// Skill Types
export interface Skill {
  element_name: string;
  element_type: string;
}

export interface SkillsByType {
  Skill?: string[];
  Ability?: string[];
  Knowledge?: string[];
  Task?: string[];
}

export interface JobBySkill {
  onet_soc_code: string;
  title: string;
  description: string;
  data_value: number;
  element_type: string;
}

// Gap Analysis Types
export interface UserSkill {
  skill_name: string;
  proficiency: number;
}

export interface GapAnalysisItem {
  skill_name: string;
  element_type: string;
  required_level: number;
  user_level: number;
  gap: number;
  status: 'met' | 'partial' | 'missing';
}

export interface GapAnalysisResult {
  target_job_code: string;
  readiness_score: number;
  total_competencies: number;
  matched_count: number;
  missing_count: number;
  gap_details: GapAnalysisItem[];
  top_gaps: GapAnalysisItem[];
}

// Compare Types
export interface CompareJob {
  onet_soc_code: string;
  title: string;
  description: string;
  competencies: {
    [key: string]: { element_name: string; data_value: number }[];
  };
}

export interface CompareResult {
  jobs: CompareJob[];
  common_competencies: string[];
  unique_competencies: string[][];
}

// Stats Types
export interface Stats {
  total_jobs: number;
  total_skills: number;
  total_abilities: number;
  total_knowledge: number;
  total_tasks: number;
}

// Follow-up Suggestion Type
export interface FollowUpSuggestion {
  text: string;
  action: string;
  type: 'compare' | 'skills' | 'career' | 'similar' | 'gap_analysis';
}

// Similar Job Type
export interface SimilarJob {
  onet_soc_code: string;
  title: string;
  similarity_score: number;
}

// Chat Types
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  analysis?: {
    structural_diagram?: {
      nodes: Array<{ id: number; label: string; group: string }>;
      edges: Array<{ from: number; to: number }>;
    };
  };
  matchedJob?: string;
  similarJobs?: SimilarJob[];
  followUpSuggestions?: FollowUpSuggestion[];
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

// Search Types
export interface SearchResult {
  jobs: { onet_soc_code: string; title: string }[];
  skills: { element_name: string; element_type: string }[];
}
