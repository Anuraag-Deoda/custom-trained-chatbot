import { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { GitCompare, X, ArrowRight, CheckCircle, Circle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import Badge from '../components/ui/Badge';
import { LoadingScreen } from '../components/ui/Spinner';
import { useJobStore } from '../store/useJobStore';
import { compareJobs } from '../lib/api';
import type { CompareResult } from '../types';

export default function Compare() {
  const [searchParams] = useSearchParams();
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  const [compareResult, setCompareResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);

  const { jobs, fetchJobs } = useJobStore();

  useEffect(() => {
    fetchJobs({ limit: 200 });
  }, [fetchJobs]);

  useEffect(() => {
    const jobParam = searchParams.get('job');
    if (jobParam && !selectedJobs.includes(jobParam)) {
      setSelectedJobs([jobParam]);
    }
  }, [searchParams]);

  const handleAddJob = (jobCode: string | null) => {
    if (jobCode && !selectedJobs.includes(jobCode) && selectedJobs.length < 4) {
      setSelectedJobs([...selectedJobs, jobCode]);
    }
  };

  const handleRemoveJob = (jobCode: string) => {
    setSelectedJobs(selectedJobs.filter((j) => j !== jobCode));
    setCompareResult(null);
  };

  const handleCompare = async () => {
    if (selectedJobs.length < 2) return;

    setLoading(true);
    try {
      const result = await compareJobs(selectedJobs);
      setCompareResult(result);
    } catch (error) {
      console.error('Compare failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const availableJobs = jobs.filter((j) => !selectedJobs.includes(j.onet_soc_code));
  const jobOptions = availableJobs.map((job) => ({
    value: job.onet_soc_code,
    label: job.title,
  }));

  const selectedJobDetails = selectedJobs.map(
    (code) => jobs.find((j) => j.onet_soc_code === code)
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg">
            <GitCompare className="w-6 h-6 text-white" />
          </div>
          Compare Jobs
        </h1>
        <p className="text-gray-500 mt-1">
          Compare up to 4 job roles side by side
        </p>
      </div>

      {/* Job Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Jobs to Compare</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Selected Jobs */}
          <div className="flex flex-wrap gap-2">
            {selectedJobDetails.map(
              (job, idx) =>
                job && (
                  <motion.div
                    key={job.onet_soc_code}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="flex items-center gap-2 px-3 py-2 bg-primary-50 border border-primary-200 rounded-lg"
                  >
                    <span className="w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                      {idx + 1}
                    </span>
                    <span className="text-primary-900 font-medium">{job.title}</span>
                    <button
                      onClick={() => handleRemoveJob(job.onet_soc_code)}
                      className="p-1 text-primary-600 hover:text-red-500 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </motion.div>
                )
            )}
          </div>

          {/* Add More */}
          {selectedJobs.length < 4 && (
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <Select
                  options={jobOptions}
                  value={null}
                  onChange={handleAddJob}
                  placeholder="Add a job to compare..."
                  label={`Job ${selectedJobs.length + 1}`}
                />
              </div>
            </div>
          )}

          {/* Compare Button */}
          <div className="flex justify-center pt-4">
            <Button
              size="lg"
              onClick={handleCompare}
              disabled={selectedJobs.length < 2}
              loading={loading}
            >
              <GitCompare className="w-5 h-5" />
              Compare {selectedJobs.length} Jobs
              <ArrowRight className="w-5 h-5" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {loading && <LoadingScreen message="Comparing jobs..." />}

      {compareResult && !loading && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* Job Cards */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {compareResult.jobs.map((job, idx) => (
              <Card key={job.onet_soc_code}>
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold">
                      {idx + 1}
                    </span>
                    <CardTitle className="text-base">{job.title}</CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {Object.entries(job.competencies).slice(0, 3).map(([type, comps]) => (
                    <div key={type}>
                      <p className="text-xs font-medium text-gray-500 uppercase mb-1">
                        Top {type}s
                      </p>
                      <div className="space-y-1">
                        {comps.slice(0, 3).map((comp) => (
                          <div
                            key={comp.element_name}
                            className="flex items-center justify-between text-sm"
                          >
                            <span className="text-gray-700 truncate">
                              {comp.element_name}
                            </span>
                            <span className="text-primary-600 font-medium">
                              {comp.data_value.toFixed(1)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                  <Link
                    to={`/jobs/${job.onet_soc_code}`}
                    className="text-primary-600 text-sm font-medium hover:underline"
                  >
                    View full details →
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Common Competencies */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                Common Competencies ({compareResult.common_competencies.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {compareResult.common_competencies.length === 0 ? (
                <p className="text-gray-500">No common competencies found</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {compareResult.common_competencies.map((comp) => (
                    <Badge key={comp} variant="success">
                      {comp}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Unique Competencies */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Circle className="w-5 h-5 text-purple-500" />
                Unique Competencies by Job
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {compareResult.jobs.map((job, idx) => (
                <div key={job.onet_soc_code}>
                  <p className="font-medium text-gray-900 mb-2">{job.title}</p>
                  <div className="flex flex-wrap gap-2">
                    {compareResult.unique_competencies[idx]?.slice(0, 10).map((comp) => (
                      <Badge key={comp} variant="primary">
                        {comp}
                      </Badge>
                    ))}
                    {(compareResult.unique_competencies[idx]?.length || 0) > 10 && (
                      <Badge variant="default">
                        +{compareResult.unique_competencies[idx].length - 10} more
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
