import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Briefcase, ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { Card, CardContent } from '../components/ui/Card';
import Button from '../components/ui/Button';
import { SearchInput } from '../components/ui/Input';
import { useJobStore } from '../store/useJobStore';
import { LoadingScreen } from '../components/ui/Spinner';
import { debounce, truncate } from '../lib/utils';

export default function Jobs() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('search') || '');

  const { jobs, loading, pagination, fetchJobs } = useJobStore();

  const debouncedSearch = debounce((query: string) => {
    setSearchParams(query ? { search: query } : {});
    fetchJobs({ search: query, page: 1 });
  }, 300);

  useEffect(() => {
    fetchJobs({
      search: searchParams.get('search') || '',
      page: Number(searchParams.get('page')) || 1,
    });
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    debouncedSearch(value);
  };

  const handlePageChange = (newPage: number) => {
    fetchJobs({ search: searchQuery, page: newPage });
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (loading && jobs.length === 0) {
    return <LoadingScreen message="Loading jobs..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Job Explorer</h1>
          <p className="text-gray-500 mt-1">
            Browse {pagination.total.toLocaleString()} job roles
          </p>
        </div>
        <div className="w-full sm:w-80">
          <SearchInput
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder="Search job titles..."
          />
        </div>
      </div>

      {/* Jobs Grid */}
      {jobs.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Search className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">No jobs found</h3>
            <p className="text-gray-500">Try adjusting your search query</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {jobs.map((job, index) => (
            <motion.div
              key={job.onet_soc_code}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Link to={`/jobs/${job.onet_soc_code}`}>
                <Card hover className="h-full">
                  <CardContent className="p-5">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-primary-50 rounded-lg shrink-0">
                        <Briefcase className="w-5 h-5 text-primary-600" />
                      </div>
                      <div className="min-w-0">
                        <h3 className="font-semibold text-gray-900 mb-1 truncate">
                          {job.title}
                        </h3>
                        <p className="text-sm text-gray-500 line-clamp-2">
                          {truncate(job.description || 'No description available', 100)}
                        </p>
                        <p className="text-xs text-gray-400 mt-2">
                          {job.onet_soc_code}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Page {pagination.page} of {pagination.pages}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page - 1)}
              disabled={pagination.page === 1}
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(pagination.page + 1)}
              disabled={pagination.page === pagination.pages}
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
