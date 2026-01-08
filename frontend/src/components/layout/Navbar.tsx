import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, User, Menu } from 'lucide-react';
import { search } from '../../lib/api';
import type { SearchResult } from '../../types';
import { debounce } from '../../lib/utils';
import { ElementTypeBadge } from '../ui/Badge';

interface NavbarProps {
  onMenuClick?: () => void;
}

export default function Navbar({ onMenuClick }: NavbarProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const performSearch = debounce(async (q: string) => {
    if (q.length < 2) {
      setResults(null);
      return;
    }

    setLoading(true);
    try {
      const data = await search(q, 'all', 8);
      setResults(data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  }, 300);

  useEffect(() => {
    performSearch(query);
  }, [query]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowResults(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleJobClick = (onetCode: string) => {
    setShowResults(false);
    setQuery('');
    navigate(`/jobs/${onetCode}`);
  };

  const handleSkillClick = (skillName: string) => {
    setShowResults(false);
    setQuery('');
    navigate(`/skill-mapper?skill=${encodeURIComponent(skillName)}`);
  };

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      {/* Left Section */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Search */}
        <div ref={searchRef} className="relative w-80">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => setShowResults(true)}
              placeholder="Search jobs, skills..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>

          {/* Search Results Dropdown */}
          {showResults && (query.length >= 2 || results) && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden z-50">
              {loading ? (
                <div className="px-4 py-3 text-center text-gray-500">Searching...</div>
              ) : results && (results.jobs.length > 0 || results.skills.length > 0) ? (
                <div className="max-h-96 overflow-y-auto">
                  {results.jobs.length > 0 && (
                    <div>
                      <div className="px-4 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
                        Jobs
                      </div>
                      {results.jobs.map((job) => (
                        <button
                          key={job.onet_soc_code}
                          onClick={() => handleJobClick(job.onet_soc_code)}
                          className="w-full px-4 py-2 text-left hover:bg-gray-50 transition-colors"
                        >
                          <span className="text-gray-900">{job.title}</span>
                        </button>
                      ))}
                    </div>
                  )}
                  {results.skills.length > 0 && (
                    <div>
                      <div className="px-4 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase">
                        Skills
                      </div>
                      {results.skills.map((skill, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSkillClick(skill.element_name)}
                          className="w-full px-4 py-2 text-left hover:bg-gray-50 transition-colors flex items-center justify-between"
                        >
                          <span className="text-gray-900">{skill.element_name}</span>
                          <ElementTypeBadge type={skill.element_type} />
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ) : query.length >= 2 ? (
                <div className="px-4 py-3 text-center text-gray-500">No results found</div>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-3">
        <button className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>
        <button className="p-2 rounded-lg text-gray-500 hover:bg-gray-100">
          <User className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
