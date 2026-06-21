'use client';

import { JobPostingForm } from '@/components/JobPostingForm';
import { JobBoard } from '@/components/JobBoard';

export default function WorkPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Local Work Intake</h1>
          <p className="text-lg text-gray-600">
            Post jobs or accept work • Same-day execution • $500+ daily potential
          </p>
        </div>

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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <JobPostingForm />
          </div>

          <div>
            <JobBoard />
          </div>
        </div>

        <div className="mt-12 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="flex items-center justify-center w-10 h-10 bg-blue-100 text-blue-900 font-bold rounded-full mb-3">
                1
              </div>
              <h3 className="font-semibold mb-2">Post a Job</h3>
              <p className="text-sm text-gray-600">
                Fill out the form with job details. Minimum pay: $300, maximum route distance: 35 miles.
              </p>
            </div>
            <div>
              <div className="flex items-center justify-center w-10 h-10 bg-blue-100 text-blue-900 font-bold rounded-full mb-3">
                2
              </div>
              <h3 className="font-semibold mb-2">Accept Jobs</h3>
              <p className="text-sm text-gray-600">
                Browse available jobs and confirm pay, route, scope, risk, and approval before accepting.
              </p>
            </div>
            <div>
              <div className="flex items-center justify-center w-10 h-10 bg-blue-100 text-blue-900 font-bold rounded-full mb-3">
                3
              </div>
              <h3 className="font-semibold mb-2">Complete & Track</h3>
              <p className="text-sm text-gray-600">
                Execute the job, document proof of work, and track payment status before closing it out.
              </p>
            </div>
          </div>
        </div>

        <div className="mt-8 bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">FAQ</h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold mb-2">How much can I earn?</h3>
              <p className="text-sm text-gray-600">
                Target stack is $500+ daily revenue by combining field dispatch, hauling, and local service work.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Is this protected by login?</h3>
              <p className="text-sm text-gray-600">
                Login is temporarily disabled while the backend and auth stack are repaired. Do not store sensitive customer data here.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">How do payments work?</h3>
              <p className="text-sm text-gray-600">
                Payment links, deposits, and invoices must be verified through the approved payment platform before dispatch.
              </p>
            </div>
          </div>
        </div>
      </div>

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
