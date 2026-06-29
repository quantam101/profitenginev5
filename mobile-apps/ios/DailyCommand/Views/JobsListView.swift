import SwiftUI
import MapKit

struct JobsListView: View {
    @EnvironmentObject var jobService: JobService
    @State private var selectedJob: Job?
    @State private var showJobDetail = false

    var body: some View {
        NavigationView {
            ZStack {
                if jobService.isLoading && jobService.jobs.isEmpty {
                    ProgressView()
                        .scaleEffect(1.5)
                } else if jobService.jobs.isEmpty {
                    VStack {
                        Image(systemName: "briefcase.fill")
                            .font(.system(size: 50))
                            .foregroundColor(.gray)
                        Text("No jobs assigned")
                            .font(.headline)
                        Text("Check back later for new assignments")
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color(.systemBackground))
                } else {
                    List {
                        // Today's Stats Section
                        if let stats = jobService.todayStats {
                            HStack {
                                VStack(alignment: .leading) {
                                    Text("Today's Earnings")
                                        .font(.caption)
                                        .foregroundColor(.gray)
                                    Text("$\(String(format: "%.2f", stats.earnings))")
                                        .font(.title2)
                                        .fontWeight(.bold)
                                }
                                Spacer()
                                VStack(alignment: .trailing) {
                                    Text("Jobs Completed")
                                        .font(.caption)
                                        .foregroundColor(.gray)
                                    Text("\(stats.completedJobs)/\(stats.totalJobs)")
                                        .font(.title2)
                                        .fontWeight(.bold)
                                }
                            }
                            .padding(.vertical, 8)
                        }

                        // Jobs Section
                        ForEach(jobService.jobs) { job in
                            NavigationLink(destination: JobDetailView(job: job)) {
                                JobListItemView(job: job)
                            }
                            .onTapGesture {
                                selectedJob = job
                            }
                        }
                    }
                    .listStyle(.plain)
                }

                if let errorMessage = jobService.errorMessage {
                    VStack {
                        HStack {
                            Image(systemName: "exclamationmark.circle.fill")
                                .foregroundColor(.red)
                            Text(errorMessage)
                                .font(.caption)
                            Spacer()
                            Button(action: { jobService.errorMessage = nil }) {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundColor(.gray)
                            }
                        }
                        .padding()
                        .background(Color(.systemRed).opacity(0.1))
                        .cornerRadius(8)
                        .padding()
                        Spacer()
                    }
                }
            }
            .navigationTitle("Today's Jobs")
            .refreshable {
                await jobService.fetchTodayJobs()
            }
            .onAppear {
                jobService.startRealTimeUpdates()
            }
            .onDisappear {
                jobService.stopRealTimeUpdates()
            }
        }
    }
}

struct JobListItemView: View {
    let job: Job

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(job.customerName)
                        .font(.headline)
                    HStack {
                        Image(systemName: "mappin.circle.fill")
                            .font(.caption)
                            .foregroundColor(.blue)
                        Text(job.address)
                            .font(.caption)
                            .foregroundColor(.gray)
                            .lineLimit(1)
                    }
                }
                Spacer()
                VStack(alignment: .trailing) {
                    StatusBadge(status: job.status)
                    Text("\(job.estimatedDuration) min")
                        .font(.caption)
                        .foregroundColor(.gray)
                }
            }
        }
        .padding(.vertical, 8)
    }
}

struct StatusBadge: View {
    let status: JobStatus

    var backgroundColor: Color {
        switch status {
        case .pending:
            return Color.yellow.opacity(0.2)
        case .enRoute:
            return Color.blue.opacity(0.2)
        case .onSite:
            return Color.orange.opacity(0.2)
        case .completed:
            return Color.green.opacity(0.2)
        case .cancelled:
            return Color.red.opacity(0.2)
        }
    }

    var textColor: Color {
        switch status {
        case .pending:
            return Color.yellow
        case .enRoute:
            return Color.blue
        case .onSite:
            return Color.orange
        case .completed:
            return Color.green
        case .cancelled:
            return Color.red
        }
    }

    var body: some View {
        Text(status.rawValue.capitalized)
            .font(.caption)
            .fontWeight(.semibold)
            .foregroundColor(textColor)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(backgroundColor)
            .cornerRadius(4)
    }
}

#Preview {
    JobsListView()
        .environmentObject(JobService())
}
