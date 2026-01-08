import { useState, useEffect } from 'react';
import { X, Plus, Trash2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Button from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { ElementTypeBadge } from '../ui/Badge';
import { useSkillStore } from '../../store/useSkillStore';
import { getSkills } from '../../lib/api';
import type { Skill } from '../../types';
import { debounce } from '../../lib/utils';

export default function UserSkillInput() {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Skill[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const { userSkills, addUserSkill, removeUserSkill, updateUserSkillProficiency, clearUserSkills } =
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

  const handleAddSkill = (skill: Skill) => {
    addUserSkill({ skill_name: skill.element_name, proficiency: 5 });
    setSearchQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Your Skills</CardTitle>
        {userSkills.length > 0 && (
          <Button variant="ghost" size="sm" onClick={clearUserSkills}>
            <Trash2 className="w-4 h-4 mr-1" />
            Clear All
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search Input */}
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setShowSuggestions(true)}
            placeholder="Search and add your skills..."
            className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
          />
          <Plus className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />

          {/* Suggestions Dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-lg border border-gray-200 max-h-60 overflow-y-auto z-10">
              {suggestions.map((skill, idx) => {
                const alreadyAdded = userSkills.some(
                  (s) => s.skill_name.toLowerCase() === skill.element_name.toLowerCase()
                );

                return (
                  <button
                    key={idx}
                    onClick={() => !alreadyAdded && handleAddSkill(skill)}
                    disabled={alreadyAdded}
                    className={`w-full px-4 py-2 text-left flex items-center justify-between hover:bg-gray-50 ${
                      alreadyAdded ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    <span className="text-gray-900">{skill.element_name}</span>
                    <div className="flex items-center gap-2">
                      <ElementTypeBadge type={skill.element_type} />
                      {alreadyAdded && (
                        <span className="text-xs text-gray-400">Added</span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Skills List */}
        {userSkills.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p className="mb-2">No skills added yet</p>
            <p className="text-sm">Search and add skills to get started with gap analysis</p>
          </div>
        ) : (
          <div className="space-y-2">
            <AnimatePresence>
              {userSkills.map((skill) => (
                <motion.div
                  key={skill.skill_name}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {skill.skill_name}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={skill.proficiency}
                      onChange={(e) =>
                        updateUserSkillProficiency(skill.skill_name, Number(e.target.value))
                      }
                      className="w-24 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
                    />
                    <span className="text-sm font-medium text-primary-600 w-6 text-center">
                      {skill.proficiency}
                    </span>
                    <button
                      onClick={() => removeUserSkill(skill.skill_name)}
                      className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}

        <p className="text-xs text-gray-500">
          Added {userSkills.length} skill{userSkills.length !== 1 ? 's' : ''}
        </p>
      </CardContent>
    </Card>
  );
}
