import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Briefcase,
  Wrench,
  Zap,
  BookOpen,
  CheckSquare,
  ArrowRight,
  Map,
  GitCompare,
  MessageSquare,
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import { useJobStore } from '../store/useJobStore';
import { formatNumber } from '../lib/utils';
import Spinner from '../components/ui/Spinner';

const quickActions = [
  {
    title: 'Skill Mapper',
    description: 'Map skills to jobs and analyze gaps',
    icon: Map,
    href: '/skill-mapper',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    title: 'Compare Jobs',
    description: 'Side-by-side job comparison',
    icon: GitCompare,
    href: '/compare',
    color: 'from-purple-500 to-pink-500',
  },
  {
    title: 'AI Chat',
    description: 'Ask questions about any role',
    icon: MessageSquare,
    href: '/chat',
    color: 'from-orange-500 to-red-500',
  },
];

const popularJobs = [
  'Data Scientist',
  'Software Developer',
  'Financial Manager',
  'Marketing Manager',
  'Project Manager',
  'Business Analyst',
];

export default function Dashboard() {
  const { stats, fetchStats } = useJobStore();

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const statCards = [
    { label: 'Total Jobs', value: stats?.total_jobs, icon: Briefcase, color: 'bg-blue-500' },
    { label: 'Skills', value: stats?.total_skills, icon: Wrench, color: 'bg-green-500' },
    { label: 'Abilities', value: stats?.total_abilities, icon: Zap, color: 'bg-purple-500' },
    { label: 'Knowledge Areas', value: stats?.total_knowledge, icon: BookOpen, color: 'bg-orange-500' },
    { label: 'Tasks', value: stats?.total_tasks, icon: CheckSquare, color: 'bg-pink-500' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Welcome to the Competency Model Explorer</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {statCards.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${stat.color}`}>
                    <stat.icon className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-gray-900">
                      {stat.value !== undefined ? formatNumber(stat.value) : <Spinner size="sm" />}
                    </p>
                    <p className="text-xs text-gray-500">{stat.label}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {quickActions.map((action, index) => (
            <motion.div
              key={action.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + index * 0.1 }}
            >
              <Link to={action.href}>
                <Card hover className="h-full">
                  <CardContent className="p-6">
                    <div
                      className={`w-12 h-12 bg-gradient-to-br ${action.color} rounded-xl flex items-center justify-center mb-4`}
                    >
                      <action.icon className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="font-semibold text-gray-900 mb-1">{action.title}</h3>
                    <p className="text-sm text-gray-500">{action.description}</p>
                    <div className="flex items-center gap-1 mt-4 text-primary-600 text-sm font-medium">
                      Get Started
                      <ArrowRight className="w-4 h-4" />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Popular Jobs */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Popular Job Searches</h2>
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-2">
              {popularJobs.map((job) => (
                <Link
                  key={job}
                  to={`/jobs?search=${encodeURIComponent(job)}`}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-full text-sm font-medium text-gray-700 transition-colors"
                >
                  {job}
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Feature Highlight */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <Card className="bg-gradient-to-br from-primary-600 to-purple-700 border-0">
          <CardContent className="p-8 text-white">
            <div className="max-w-2xl">
              <h2 className="text-2xl font-bold mb-3">Discover Your Perfect Career Match</h2>
              <p className="text-white/80 mb-6">
                Use our advanced Skill Mapper to input your current skills and find the best matching
                jobs. Get detailed gap analysis and personalized recommendations for your career
                development.
              </p>
              <Link
                to="/skill-mapper"
                className="inline-flex items-center gap-2 bg-white text-primary-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                <Map className="w-5 h-5" />
                Try Skill Mapper
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
