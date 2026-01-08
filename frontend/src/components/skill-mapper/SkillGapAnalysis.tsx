import { motion } from 'framer-motion';
import {
  CheckCircle,
  AlertCircle,
  XCircle,
  TrendingUp,
  Target,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import Badge from '../ui/Badge';
import SkillRadarChart from './SkillRadarChart';
import type { GapAnalysisResult } from '../../types';

interface SkillGapAnalysisProps {
  result: GapAnalysisResult;
  jobTitle?: string;
}

export default function SkillGapAnalysis({ result, jobTitle: _jobTitle }: SkillGapAnalysisProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'met':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'partial':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <XCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'met':
        return <Badge variant="success">Met</Badge>;
      case 'partial':
        return <Badge variant="warning">Partial</Badge>;
      default:
        return <Badge variant="danger">Missing</Badge>;
    }
  };

  const radarData = result.gap_details.slice(0, 10).map((item) => ({
    skill: item.skill_name,
    required: item.required_level,
    current: item.user_level,
  }));

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card>
            <CardContent className="p-4 text-center">
              <div
                className={`text-4xl font-bold mb-1 ${
                  result.readiness_score >= 70
                    ? 'text-green-600'
                    : result.readiness_score >= 40
                    ? 'text-yellow-600'
                    : 'text-red-600'
                }`}
              >
                {result.readiness_score}%
              </div>
              <p className="text-sm text-gray-500">Readiness Score</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-4xl font-bold text-gray-900 mb-1">
                {result.total_competencies}
              </div>
              <p className="text-sm text-gray-500">Total Competencies</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-4xl font-bold text-green-600 mb-1">
                {result.matched_count}
              </div>
              <p className="text-sm text-gray-500">Skills You Have</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardContent className="p-4 text-center">
              <div className="text-4xl font-bold text-red-600 mb-1">
                {result.missing_count}
              </div>
              <p className="text-sm text-gray-500">Skills to Learn</p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Radar Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-primary-600" />
              Skill Comparison
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SkillRadarChart data={radarData} />
          </CardContent>
        </Card>
      </motion.div>

      {/* Top Gaps */}
      {result.top_gaps.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-red-500" />
                Top Skills to Develop
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {result.top_gaps.map((gap, idx) => (
                  <div
                    key={gap.skill_name}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-6 h-6 bg-red-100 text-red-600 rounded-full flex items-center justify-center text-sm font-medium">
                        {idx + 1}
                      </span>
                      <div>
                        <p className="font-medium text-gray-900">{gap.skill_name}</p>
                        <p className="text-sm text-gray-500">{gap.element_type}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm">
                        <span className="text-gray-500">Gap: </span>
                        <span className="font-medium text-red-600">+{gap.gap.toFixed(1)}</span>
                      </p>
                      <p className="text-xs text-gray-400">
                        {gap.user_level.toFixed(1)} → {gap.required_level.toFixed(1)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Detailed Breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Detailed Skill Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {result.gap_details.map((item, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {getStatusIcon(item.status)}
                    <div>
                      <p className="font-medium text-gray-900">{item.skill_name}</p>
                      <p className="text-xs text-gray-500">{item.element_type}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm text-gray-600">
                        {item.user_level.toFixed(1)} / {item.required_level.toFixed(1)}
                      </p>
                    </div>
                    {getStatusBadge(item.status)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
