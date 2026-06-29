import Foundation

class JobService: NSObject, ObservableObject {
    @Published var jobs: [Job] = []
    @Published var currentJob: Job?
    @Published var todayStats: TodayStats?
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let apiService = APIService()
    private var updateTimer: Timer?

    func fetchTodayJobs() async {
        DispatchQueue.main.async {
            self.isLoading = true
        }

        do {
            let response = try await apiService.get(
                endpoint: "/api/jobs/today",
                responseType: JobsResponse.self
            )

            DispatchQueue.main.async {
                self.jobs = response.jobs
                self.todayStats = response.stats
                self.isLoading = false
            }
        } catch {
            DispatchQueue.main.async {
                self.errorMessage = "Failed to fetch jobs: \(error.localizedDescription)"
                self.isLoading = false
            }
        }
    }

    func startJob(_ job: Job) async {
        do {
            let response = try await apiService.post(
                endpoint: "/api/jobs/\(job.id)/start",
                body: [:],
                responseType: JobResponse.self
            )

            DispatchQueue.main.async {
                self.currentJob = response.job
                self.updateJobInList(response.job)
            }
        } catch {
            DispatchQueue.main.async {
                self.errorMessage = "Failed to start job: \(error.localizedDescription)"
            }
        }
    }

    func completeJob(_ job: Job, photos: [Data], notes: String) async {
        do {
            var body: [String: Any] = [
                "notes": notes,
                "photoCount": photos.count,
                "completedAt": ISO8601DateFormatter().string(from: Date())
            ]

            let response = try await apiService.post(
                endpoint: "/api/jobs/\(job.id)/complete",
                body: body,
                responseType: JobResponse.self
            )

            // Upload photos
            for (index, photo) in photos.enumerated() {
                _ = try await apiService.uploadPhoto(
                    endpoint: "/api/jobs/\(job.id)/photos",
                    photo: photo,
                    index: index
                )
            }

            DispatchQueue.main.async {
                self.currentJob = nil
                self.updateJobInList(response.job)
                self.fetchTodayStats()
            }
        } catch {
            DispatchQueue.main.async {
                self.errorMessage = "Failed to complete job: \(error.localizedDescription)"
            }
        }
    }

    func updateJobStatus(_ job: Job, status: JobStatus) async {
        do {
            let response = try await apiService.post(
                endpoint: "/api/jobs/\(job.id)/status",
                body: ["status": status.rawValue],
                responseType: JobResponse.self
            )

            DispatchQueue.main.async {
                self.updateJobInList(response.job)
            }
        } catch {
            DispatchQueue.main.async {
                self.errorMessage = "Failed to update status: \(error.localizedDescription)"
            }
        }
    }

    func startRealTimeUpdates() {
        updateTimer = Timer.scheduledTimer(withTimeInterval: 5, repeats: true) { [weak self] _ in
            Task {
                await self?.fetchTodayJobs()
            }
        }
    }

    func stopRealTimeUpdates() {
        updateTimer?.invalidate()
        updateTimer = nil
    }

    private func updateJobInList(_ updatedJob: Job) {
        if let index = jobs.firstIndex(where: { $0.id == updatedJob.id }) {
            jobs[index] = updatedJob
        }
    }

    private func fetchTodayStats() {
        Task {
            await fetchTodayJobs()
        }
    }

    deinit {
        stopRealTimeUpdates()
    }
}

// MARK: - Models

struct Job: Codable, Identifiable {
    let id: String
    let customerId: String
    let customerName: String
    let address: String
    let latitude: Double
    let longitude: Double
    let jobType: String
    let priority: Int
    let estimatedDuration: Int
    let status: JobStatus
    let notes: String?
    var assignedAt: Date
    var startedAt: Date?
    var completedAt: Date?
}

enum JobStatus: String, Codable {
    case pending
    case enRoute = "en_route"
    case onSite = "on_site"
    case completed
    case cancelled
}

struct TodayStats: Codable {
    let totalJobs: Int
    let completedJobs: Int
    let earnings: Double
    let averageRating: Double
}

struct JobsResponse: Codable {
    let jobs: [Job]
    let stats: TodayStats
}

struct JobResponse: Codable {
    let job: Job
}
