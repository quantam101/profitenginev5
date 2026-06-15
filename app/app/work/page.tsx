'use client';

import { JobPostingForm } from '@/components/JobPostingForm';
import { JobBoard } from '@/components/JobBoard';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function WorkPage() {
  const { data: session, status } = useSession();
  const router = useRouter();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/api/auth/signin?callbackUrl=/work');
    }
  }, [status, router]);

  if (status === 'loading' || !session) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Local Work Intake</h1>
          <p className="text-lg text-gray-600">
            Post jobs or accept work • Same-day execution • $500+ daily potential
          </p>
        </div>

        {/* Daily Target Status */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <h2 className="text-xl font-semibold text-blue-900 mb-4">Today&apos;s Target</h2>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-blue-600">Target Revenue</p>
              <p className="text-3xl font-bold text-blue-900">$500</p>
            </div>
            <div>
              <p className="text-sm text-blue-600">Deadline</p>
              <p className="text-3xl font-bold text-blue-900">12:00&nbsp;PM</p>
            </div>
            <div>
              <p className="text-sm text-blue-600">Current Time</p>
              <p className="text-3xl font-bold text-blue-900" id="current-time">
                --:-- --
              </p>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Job Posting Form */}
          <div>
            <JobPostingForm />
          </div>

          {/* Job Board */}
          <div>
            <JobBoard />
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-12 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="flex items-center justify-center w-10 h-10 bg-blue-100 text-blue-900 font-bold rounded-full mb-3">
                1
              </div>
              <h3 className="font-semibold mb-2">Post a Job</h3>
              <p className="text-sm text-gray-600">
                Fill out the form with job details. Minimum pay: $300, Maximum distance: 35 miles.
              </p>
            </div>
            <div>
              <div className="flex items-center justify-center w-10 h-10 bg-blue-100 text-blue-900 font-bold rounded-full mb-3">
                2
              </div>
              <h3 className="font-semibold mb-2">Accept Jobs</h3>
              <p className="text-sm text-gray-600">
                Browse available jobs and click &quot;Accept Job&quot; to lock it in. Jobs must be completed same-day.
              </p>
            </div>
            <div>
              <div className="flex items-center justify-center w-10 h-10 bg-blue-100 text-blue-900 font-bold rounded-full mb-3">
                3
              </div>
              <h3 className="font-semibold mb-2">Complete & Get Paid</h3>
              <p className="text-sm text-gray-600">
                Execute the job, collect payment same-day via Stripe. Deposits arrive instantly.
              </p>
            </div>
          </div>
        </div>

        {/* FAQ */}
        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">FAQ</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">How much can I earn?</h3>
              <p className="text-sm text-gray-600">
                Typical jobs pay $300&ndash;$500 with 2&ndash;4 hour duration. Experienced contractors can complete 2&ndash;3 jobs per day.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Do you take a commission?</h3>
              <p className="text-sm text-gray-600">
                No commission. Jobs are free to post and accept. We keep 100% of the reputation value.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">How do I get paid?</h3>
              <p className="text-sm text-gray-600">
                Customers pay via Stripe during or immediately after the job. Deposits hit your account same-day.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Clock script */}
      <script
        dangerouslySetInnerHTML={{
          __html: `
            document.addEventListener('DOMContentLoaded', function() {
              function updateTime() {
                const now = new Date();
                const timeElement = document.getElementById('current-time');
                if (timeElement) {
                  timeElement.textContent = now.toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: true
                  });
                }
              }
              updateTime();
              setInterval(updateTime, 1000);
            });
          `,
        }}
      />
    </div>
  );
}
