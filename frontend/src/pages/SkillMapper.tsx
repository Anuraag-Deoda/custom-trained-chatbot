import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Map, ArrowRight, Briefcase, Wrench, Target } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Tabs from '../components/ui/Tabs';
import Select from '../components/ui/Select';
import UserSkillInput from '../components/skill-mapper/UserSkillInput';
import SkillGapAnalysis from '../components/skill-mapper/SkillGapAnalysis';
import SkillToJobsView from '../components/skill-mapper/SkillToJobsView';
import { LoadingScreen } from '../components/ui/Spinner';
import { useSkillStore } from '../store/useSkillStore';
import { useJobStore } from '../store/useJobStore';

export default function SkillMapper() {
  const [searchParams] = useSearchParams();
  const [selectedJobCode, setSelectedJobCode] = useState<string | null>(
    searchParams.get('job')
  );
  const [activeView, setActiveView] = useState<'job-to-skills' | 'skill-to-jobs'>('job-to-skills');

  const {
    userSkills,
    gapAnalysis,
    loading: skillLoading,
    runGapAnalysis,
    clearGapAnalysis,
    fetchJobsForSkill,
    setSelectedSkill,
  } = useSkillStore();

  const { jobs, fetchJobs, selectedJob, fetchJobDetail } = useJobStore();

  // Load jobs for selection
  useEffect(() => {
    fetchJobs({ limit: 100 });
  }, [fetchJobs]);

  // Handle initial skill from URL
  useEffect(() => {
    const skillParam = searchParams.get('skill');
    if (skillParam) {
      setActiveView('skill-to-jobs');
      setSelectedSkill(skillParam);
      fetchJobsForSkill(skillParam);
    }
  }, [searchParams, setSelectedSkill, fetchJobsForSkill]);

  // Load job details when selected
  useEffect(() => {
    if (selectedJobCode) {
      fetchJobDetail(selectedJobCode);
    }
  }, [selectedJobCode, fetchJobDetail]);

  const handleRunAnalysis = () => {
    if (selectedJobCode) {
      runGapAnalysis(selectedJobCode);
    }
  };

  const jobOptions = jobs.map((job) => ({
    value: job.onet_soc_code,
    label: job.title,
    description: job.onet_soc_code,
  }));

  const tabs = [
    {
      id: 'job-to-skills',
      label: 'Job → Skills',
      icon: <Briefcase className="w-4 h-4" />,
      content: (
        <div className="space-y-6">
          {/* Job Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5 text-primary-600" />
                Select Target Job
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Select
                options={jobOptions}
                value={selectedJobCode}
                onChange={setSelectedJobCode}
                placeholder="Search and select a job..."
                label="Target Job"
              />
              {selectedJob && selectedJobCode && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-4 p-4 bg-primary-50 rounded-lg"
                >
                  <h4 className="font-medium text-primary-900">{selectedJob.title}</h4>
                  <p className="text-sm text-primary-700 mt-1 line-clamp-2">
                    {selectedJob.description}
                  </p>
                </motion.div>
              )}
            </CardContent>
          </Card>

          {/* User Skills Input */}
          <UserSkillInput />

          {/* Run Analysis Button */}
          <div className="flex justify-center">
            <Button
              size="lg"
              onClick={handleRunAnalysis}
              disabled={!selectedJobCode || userSkills.length === 0}
              loading={skillLoading}
            >
              <Map className="w-5 h-5" />
              Run Gap Analysis
              <ArrowRight className="w-5 h-5" />
            </Button>
          </div>

          {/* Gap Analysis Results */}
          {skillLoading && <LoadingScreen message="Analyzing skill gaps..." />}
          {gapAnalysis && !skillLoading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <SkillGapAnalysis result={gapAnalysis} jobTitle={selectedJob?.title} />
            </motion.div>
          )}
        </div>
      ),
    },
    {
      id: 'skill-to-jobs',
      label: 'Skill → Jobs',
      icon: <Wrench className="w-4 h-4" />,
      content: <SkillToJobsView />,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-primary-500 to-purple-600 rounded-lg">
              <Map className="w-6 h-6 text-white" />
            </div>
            Skill Mapper
          </h1>
          <p className="text-gray-500 mt-1">
            Map skills to jobs or find jobs by skill with gap analysis
          </p>
        </div>
        {gapAnalysis && (
          <Button variant="outline" onClick={clearGapAnalysis}>
            Clear Results
          </Button>
        )}
      </div>

      {/* Main Content */}
      <Tabs
        tabs={tabs}
        defaultTab={activeView}
        onChange={(tabId) => setActiveView(tabId as typeof activeView)}
      />
    </div>
  );
}
