import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Briefcase, TrendingUp, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { SearchInput } from '../ui/Input';
import Badge, { ElementTypeBadge } from '../ui/Badge';
import { LoadingScreen } from '../ui/Spinner';
import { useSkillStore } from '../../store/useSkillStore';
import { getSkills } from '../../lib/api';
import type { Skill } from '../../types';
import { debounce, truncate } from '../../lib/utils';

export default function SkillToJobsView() {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Skill[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const { selectedSkill, jobsForSkill, loading, fetchJobsForSkill } =
    useSkillStore();

  const searchSkills = debounce(async (query: string) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const result = await getSkills({ search: query });
      setSuggestions(result.all_skills.slice(0, 10));
    } catch (error) {
      console.error('Failed to search skills:', error);
    }
  }, 300);

  useEffect(() => {
    searchSkills(searchQuery);
  }, [searchQuery]);

  const handleSelectSkill = (skill: Skill) => {
    setSearchQuery(skill.element_name);
    setSuggestions([]);
    setShowSuggestions(false);
    fetchJobsForSkill(skill.element_name);
  };

  return (
    <div className="space-y-6">
      {/* Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5 text-primary-600" />
            Find Jobs by Skill
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <SearchInput
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setShowSuggestions(true)}
              placeholder="Search for a skill, ability, or knowledge area..."
            />

            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 max-h-60 overflow-y-auto z-10">
                {suggestions.map((skill, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSelectSkill(skill)}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 flex items-center justify-between border-b border-gray-100 last:border-0"
                  >
                    <span className="text-gray-900">{skill.element_name}</span>
                    <ElementTypeBadge type={skill.element_type} />
                  </button>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {loading ? (
        <LoadingScreen message="Finding jobs..." />
      ) : selectedSkill ? (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-600" />
                Jobs requiring "{selectedSkill}"
              </CardTitle>
              <Badge>{jobsForSkill.length} jobs found</Badge>
            </div>
          </CardHeader>
          <CardContent>
            {jobsForSkill.length === 0 ? (
              <p className="text-gray-500 text-center py-8">
                No jobs found requiring this skill
              </p>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {jobsForSkill.map((job, idx) => (
                  <motion.div
                    key={job.onet_soc_code}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.03 }}
                  >
                    <Link to={`/jobs/${job.onet_soc_code}`}>
                      <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                        <div className="p-2 bg-white rounded-lg shadow-sm">
                          <Briefcase className="w-5 h-5 text-primary-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-gray-900">{job.title}</h4>
                          <p className="text-sm text-gray-500 truncate">
                            {truncate(job.description || 'No description', 80)}
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="text-lg font-bold text-primary-600">
                            {job.data_value.toFixed(1)}
                          </div>
                          <p className="text-xs text-gray-500">Importance</p>
                        </div>
                      </div>
                    </Link>
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Search for a Skill
            </h3>
            <p className="text-gray-500 max-w-md mx-auto">
              Enter a skill, ability, or knowledge area above to see all jobs that
              require it, sorted by importance.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
