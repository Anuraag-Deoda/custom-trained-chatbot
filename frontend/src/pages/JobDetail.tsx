import { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Briefcase, Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge, { ElementTypeBadge } from '../components/ui/Badge';
import Tabs from '../components/ui/Tabs';
import { useJobStore } from '../store/useJobStore';
import { LoadingScreen } from '../components/ui/Spinner';
import { getScoreColor } from '../lib/utils';

export default function JobDetail() {
  const { onetCode } = useParams<{ onetCode: string }>();
  const { selectedJob, loading, fetchJobDetail, clearSelectedJob } = useJobStore();

  useEffect(() => {
    if (onetCode) {
      fetchJobDetail(onetCode);
    }
    return () => clearSelectedJob();
  }, [onetCode, fetchJobDetail, clearSelectedJob]);

  if (loading || !selectedJob) {
    return <LoadingScreen message="Loading job details..." />;
  }

  const competencyTypes = Object.keys(selectedJob.competencies || {});

  const tabs = competencyTypes.map((type) => ({
    id: type,
    label: `${type}s`,
    content: (
      <div className="space-y-3">
        {selectedJob.competencies?.[type as keyof typeof selectedJob.competencies]?.map(
          (comp, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.03 }}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center shadow-sm">
                  <span className={`text-sm font-bold ${getScoreColor(comp.data_value)}`}>
                    {comp.data_value?.toFixed(1)}
                  </span>
                </div>
                <span className="text-gray-900">{comp.element_name}</span>
              </div>
              {comp.scale_name && (
                <Badge variant="default" size="sm">
                  {comp.scale_name}
                </Badge>
              )}
            </motion.div>
          )
        )}
      </div>
    ),
  }));

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link
        to="/jobs"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Jobs
      </Link>

      {/* Job Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-gradient-to-br from-primary-500 to-purple-600 rounded-xl">
                <Briefcase className="w-8 h-8 text-white" />
              </div>
              <div className="flex-1">
                <div className="flex items-start justify-between">
                  <div>
                    <h1 className="text-2xl font-bold text-gray-900">{selectedJob.title}</h1>
                    <p className="text-gray-500 mt-1">{selectedJob.onet_soc_code}</p>
                  </div>
                  <div className="flex gap-2">
                    <Link to={`/compare?job=${selectedJob.onet_soc_code}`}>
                      <Button variant="outline" size="sm">
                        <Plus className="w-4 h-4" />
                        Compare
                      </Button>
                    </Link>
                    <Link to={`/skill-mapper?job=${selectedJob.onet_soc_code}`}>
                      <Button size="sm">Gap Analysis</Button>
                    </Link>
                  </div>
                </div>
                <p className="text-gray-600 mt-4 leading-relaxed">{selectedJob.description}</p>
                <div className="flex gap-2 mt-4">
                  {competencyTypes.map((type) => (
                    <ElementTypeBadge key={type} type={type} />
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Competencies Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Competencies</CardTitle>
          </CardHeader>
          <CardContent>
            {tabs.length > 0 ? (
              <Tabs tabs={tabs} defaultTab={tabs[0].id} />
            ) : (
              <p className="text-gray-500 text-center py-8">No competencies available</p>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
