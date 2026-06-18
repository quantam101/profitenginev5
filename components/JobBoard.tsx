'use client';

import { useEffect, useState } from 'react';
import { Job, CATEGORY_ICONS } from '@/lib/jobs';

const OPERATOR_ID = 'dispatch@alreadyherellc.com';

export function JobBoard({ refreshTrigger }: { refreshTrigger?: number }) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [accepting, setAccepting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/jobs');
      if (!res.ok) throw new Error('Failed to load jobs');
      const data = await res.json();
      setJobs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [refreshTrigger]);

  const handleAcceptJob = async (jobId: string) => {
    setAccepting(jobId);
    try {
      const res = await fetch(`/api/jobs/${jobId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'x-user-id': OPERATOR_ID,
        },
        body: JSON.stringify({ action: 'accept' }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || 'Failed to queue job for review');
      }

      await fetchJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to queue job for review');
    } finally {
      setAccepting(null);
    }
  };

  const openJobs = jobs.filter((j) => j.status === 'open');
  const operatorAcceptedJobs = jobs.filter((j) => j.status === 'accepted' && j.accepted_by_id === OPERATOR_ID);
  const operatorCompletedJobs = jobs.filter((j) => j.status === 'completed' && j.accepted_by_id === OPERATOR_ID);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-4">Available Jobs</h2>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading jobs...</div>
        ) : openJobs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">No jobs available right now</div>
        ) : (
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {openJobs.map((job) => (
              <div
                key={job.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-semibold text-lg">{job.title}</h3>
                    <p className="text-sm text-gray-600">
                      {CATEGORY_ICONS[job.category]} {job.category}
                    </p>
                  </div>
                  <p className="text-2xl font-bold text-green-600">${job.pay}</p>
                </div>

                <p className="text-sm text-gray-600 mb-2">Location: {job.location}</p>

                {job.description && (
                  <p className="text-sm text-gray-700 mb-3 line-clamp-2">{job.description}</p>
                )}

                <div className="flex justify-between items-center mb-3">
                  <div className="text-sm">
                    <p className="text-gray-600">
                      {job.miles} miles • ${job.margin.toFixed(2)} estimated margin
                    </p>
                  </div>
                  <p className="text-xs text-gray-500">
                    {new Date(job.created_at).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>

                <button
                  onClick={() => handleAcceptJob(job.id)}
                  disabled={accepting === job.id}
                  className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-2 px-3 rounded transition-colors text-sm"
                >
                  {accepting === job.id ? 'Queuing...' : 'Queue for Review'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {operatorAcceptedJobs.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">Queued Jobs</h3>
          <div className="space-y-2">
            {operatorAcceptedJobs.map((job) => (
              <div key={job.id} className="flex justify-between items-center text-sm">
                <span className="text-blue-900">{job.title}</span>
                <span className="text-blue-600 font-semibold">${job.pay}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {operatorCompletedJobs.length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-900 mb-2">Completed Jobs</h3>
          <p className="text-sm text-green-700">
            {operatorCompletedJobs.length} completed job{operatorCompletedJobs.length !== 1 ? 's' : ''} tracked on this platform
          </p>
        </div>
      )}
    </div>
  );
}
