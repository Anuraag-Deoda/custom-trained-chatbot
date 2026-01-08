import { create } from 'zustand';
import type { Job, JobDetail, Stats } from '../types';
import { getJobs, getJobDetail, getStats } from '../lib/api';

interface JobState {
  jobs: Job[];
  selectedJob: JobDetail | null;
  stats: Stats | null;
  loading: boolean;
  error: string | null;
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };

  // Actions
  fetchJobs: (params?: { page?: number; search?: string; limit?: number }) => Promise<void>;
  fetchJobDetail: (onetCode: string) => Promise<void>;
  fetchStats: () => Promise<void>;
  clearSelectedJob: () => void;
  setError: (error: string | null) => void;
}

export const useJobStore = create<JobState>((set, get) => ({
  jobs: [],
  selectedJob: null,
  stats: null,
  loading: false,
  error: null,
  pagination: {
    page: 1,
    limit: 20,
    total: 0,
    pages: 0,
  },

  fetchJobs: async (params) => {
    set({ loading: true, error: null });
    try {
      const result = await getJobs({
        page: params?.page || 1,
        limit: params?.limit || get().pagination.limit,
        search: params?.search,
      });
      set({
        jobs: result.jobs,
        pagination: result.pagination,
        loading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch jobs',
        loading: false,
      });
    }
  },

  fetchJobDetail: async (onetCode) => {
    set({ loading: true, error: null });
    try {
      const result = await getJobDetail(onetCode);
      set({
        selectedJob: { ...result.job, competencies: result.competencies },
        loading: false,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch job details',
        loading: false,
      });
    }
  },

  fetchStats: async () => {
    try {
      const stats = await getStats();
      set({ stats });
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  },

  clearSelectedJob: () => set({ selectedJob: null }),

  setError: (error) => set({ error }),
}));
