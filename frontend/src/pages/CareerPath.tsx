import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { TrendingUp, ArrowRight, Briefcase, Star, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Select from '../components/ui/Select';
import Badge from '../components/ui/Badge';
import { useJobStore } from '../store/useJobStore';

const careerPaths = [
  {
    name: 'Technology',
    color: 'from-blue-500 to-cyan-500',
    roles: ['Software Developer', 'Senior Developer', 'Tech Lead', 'Engineering Manager', 'CTO'],
  },
  {
    name: 'Finance',
    color: 'from-green-500 to-emerald-500',
    roles: ['Financial Analyst', 'Senior Analyst', 'Finance Manager', 'Director of Finance', 'CFO'],
  },
  {
    name: 'Marketing',
    color: 'from-purple-500 to-pink-500',
    roles: ['Marketing Coordinator', 'Marketing Specialist', 'Marketing Manager', 'Director of Marketing', 'CMO'],
  },
  {
    name: 'Operations',
    color: 'from-orange-500 to-red-500',
    roles: ['Operations Analyst', 'Operations Manager', 'Director of Operations', 'VP Operations', 'COO'],
  },
];

export default function CareerPath() {
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [selectedStartJob, setSelectedStartJob] = useState<string | null>(null);
  const { jobs, fetchJobs } = useJobStore();

  useEffect(() => {
    fetchJobs({ limit: 100 });
  }, [fetchJobs]);

  const jobOptions = jobs.map((job) => ({
    value: job.onet_soc_code,
    label: job.title,
  }));

  const selectedPathData = careerPaths.find((p) => p.name === selectedPath);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-green-500 to-teal-600 rounded-lg">
            <TrendingUp className="w-6 h-6 text-white" />
          </div>
          Career Path Explorer
        </h1>
        <p className="text-gray-500 mt-1">
          Explore career progressions and plan your growth
        </p>
      </div>

      {/* Career Path Selection */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {careerPaths.map((path) => (
          <motion.div
            key={path.name}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Card
              hover
              onClick={() => setSelectedPath(path.name)}
              className={selectedPath === path.name ? 'ring-2 ring-primary-500' : ''}
            >
              <CardContent className="p-4">
                <div
                  className={`w-10 h-10 bg-gradient-to-br ${path.color} rounded-lg flex items-center justify-center mb-3`}
                >
                  <Briefcase className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-semibold text-gray-900">{path.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{path.roles.length} levels</p>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Selected Path Details */}
      {selectedPathData && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Star className="w-5 h-5 text-yellow-500" />
                {selectedPathData.name} Career Path
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative">
                {/* Path Line */}
                <div className="absolute left-6 top-8 bottom-8 w-0.5 bg-gray-200" />

                {/* Path Steps */}
                <div className="space-y-6">
                  {selectedPathData.roles.map((role, idx) => (
                    <motion.div
                      key={role}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.1 }}
                      className="flex items-start gap-4"
                    >
                      <div
                        className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 z-10 ${
                          idx === 0
                            ? 'bg-green-500 text-white'
                            : idx === selectedPathData.roles.length - 1
                            ? 'bg-purple-500 text-white'
                            : 'bg-white border-2 border-gray-200 text-gray-600'
                        }`}
                      >
                        {idx + 1}
                      </div>
                      <div className="flex-1 pt-2">
                        <div className="flex items-center gap-3">
                          <h4 className="font-medium text-gray-900">{role}</h4>
                          {idx === 0 && (
                            <Badge variant="success" size="sm">
                              Entry
                            </Badge>
                          )}
                          {idx === selectedPathData.roles.length - 1 && (
                            <Badge variant="primary" size="sm">
                              Goal
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 mt-1">
                          Level {idx + 1} • {idx * 2}-{idx * 2 + 3} years experience typical
                        </p>
                        <Link
                          to={`/jobs?search=${encodeURIComponent(role)}`}
                          className="inline-flex items-center gap-1 text-primary-600 text-sm mt-2 hover:underline"
                        >
                          Find similar roles
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Custom Path Builder */}
      <Card>
        <CardHeader>
          <CardTitle>Build Your Own Path</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-500">
            Select your current role and explore potential career progressions based on
            skill overlap and industry trends.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Select
                options={jobOptions}
                value={selectedStartJob}
                onChange={setSelectedStartJob}
                placeholder="Select your current role..."
                label="Current Role"
              />
            </div>
            <div className="sm:pt-7">
              <Link to={selectedStartJob ? `/skill-mapper?job=${selectedStartJob}` : '#'}>
                <Button disabled={!selectedStartJob}>
                  Analyze Skills
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
          </div>

          {selectedStartJob && (
            <div className="mt-4 p-4 bg-primary-50 rounded-lg">
              <p className="text-sm text-primary-800">
                Use the Skill Mapper to identify gaps between your current skills and
                target roles. This will help you plan your development path.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Tips */}
      <Card className="bg-gradient-to-br from-primary-600 to-purple-700 text-white border-0">
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold mb-3">Career Growth Tips</h3>
          <ul className="space-y-2 text-white/90">
            <li className="flex items-start gap-2">
              <Star className="w-5 h-5 shrink-0 mt-0.5" />
              <span>Focus on transferable skills that apply across multiple roles</span>
            </li>
            <li className="flex items-start gap-2">
              <Star className="w-5 h-5 shrink-0 mt-0.5" />
              <span>Build expertise in high-demand areas like data analysis and leadership</span>
            </li>
            <li className="flex items-start gap-2">
              <Star className="w-5 h-5 shrink-0 mt-0.5" />
              <span>Use the Compare tool to understand skill gaps between roles</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
