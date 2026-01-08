import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Skill, SkillsByType, JobBySkill, UserSkill, GapAnalysisResult } from '../types';
import { getSkills, getJobsBySkill, analyzeGap } from '../lib/api';

interface SkillState {
  skills: Skill[];
  skillsByType: SkillsByType;
  selectedSkill: string | null;
  jobsForSkill: JobBySkill[];
  userSkills: UserSkill[];
  gapAnalysis: GapAnalysisResult | null;
  loading: boolean;
  error: string | null;

  // Actions
  fetchSkills: (params?: { type?: string; search?: string }) => Promise<void>;
  fetchJobsForSkill: (skillName: string) => Promise<void>;
  addUserSkill: (skill: UserSkill) => void;
  removeUserSkill: (skillName: string) => void;
  updateUserSkillProficiency: (skillName: string, proficiency: number) => void;
  clearUserSkills: () => void;
  runGapAnalysis: (targetJobCode: string) => Promise<void>;
  clearGapAnalysis: () => void;
  setSelectedSkill: (skill: string | null) => void;
}

export const useSkillStore = create<SkillState>()(
  persist(
    (set, get) => ({
      skills: [],
      skillsByType: {},
      selectedSkill: null,
      jobsForSkill: [],
      userSkills: [],
      gapAnalysis: null,
      loading: false,
      error: null,

      fetchSkills: async (params) => {
        set({ loading: true, error: null });
        try {
          const result = await getSkills(params);
          set({
            skills: result.all_skills,
            skillsByType: result.skills_by_type,
            loading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch skills',
            loading: false,
          });
        }
      },

      fetchJobsForSkill: async (skillName) => {
        set({ loading: true, error: null, selectedSkill: skillName });
        try {
          const result = await getJobsBySkill(skillName);
          set({
            jobsForSkill: result.jobs,
            loading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch jobs for skill',
            loading: false,
          });
        }
      },

      addUserSkill: (skill) => {
        const { userSkills } = get();
        const exists = userSkills.find(
          (s) => s.skill_name.toLowerCase() === skill.skill_name.toLowerCase()
        );
        if (!exists) {
          set({ userSkills: [...userSkills, skill] });
        }
      },

      removeUserSkill: (skillName) => {
        set({
          userSkills: get().userSkills.filter(
            (s) => s.skill_name.toLowerCase() !== skillName.toLowerCase()
          ),
        });
      },

      updateUserSkillProficiency: (skillName, proficiency) => {
        set({
          userSkills: get().userSkills.map((s) =>
            s.skill_name.toLowerCase() === skillName.toLowerCase()
              ? { ...s, proficiency }
              : s
          ),
        });
      },

      clearUserSkills: () => set({ userSkills: [] }),

      runGapAnalysis: async (targetJobCode) => {
        set({ loading: true, error: null });
        try {
          const result = await analyzeGap(targetJobCode, get().userSkills);
          set({ gapAnalysis: result, loading: false });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Gap analysis failed',
            loading: false,
          });
        }
      },

      clearGapAnalysis: () => set({ gapAnalysis: null }),

      setSelectedSkill: (skill) => set({ selectedSkill: skill }),
    }),
    {
      name: 'skill-store',
      partialize: (state) => ({ userSkills: state.userSkills }),
    }
  )
);
