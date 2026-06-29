import SwiftUI

struct JobTimerView: View {
    let job: Job
    @EnvironmentObject var jobService: JobService
    @State private var elapsedSeconds = 0
    @State private var isRunning = false
    @State private var timerTask: Task<Void, Never>?

    var formattedTime: String {
        let hours = elapsedSeconds / 3600
        let minutes = (elapsedSeconds % 3600) / 60
        let seconds = elapsedSeconds % 60
        return String(format: "%02d:%02d:%02d", hours, minutes, seconds)
    }

    var body: some View {
        ZStack {
            LinearGradient(
                gradient: Gradient(colors: [Color.blue.opacity(0.1), Color.cyan.opacity(0.1)]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(spacing: 32) {
                // Header
                VStack(spacing: 8) {
                    Text(job.customerName)
                        .font(.headline)
                    Text(job.address)
                        .font(.caption)
                        .foregroundColor(.gray)
                }

                Spacer()

                // Timer Display
                VStack(spacing: 16) {
                    ZStack {
                        Circle()
                            .stroke(Color.blue.opacity(0.2), lineWidth: 20)
                            .frame(width: 280, height: 280)

                        VStack(spacing: 16) {
                            Text(formattedTime)
                                .font(.system(size: 60, weight: .bold, design: .monospaced))
                                .foregroundColor(.blue)

                            HStack(spacing: 20) {
                                Image(systemName: "briefcase.fill")
                                    .font(.title3)
                                Text("Time on Job")
                                    .font(.caption)
                            }
                            .foregroundColor(.gray)
                        }
                    }
                }

                // Job Stats
                VStack(spacing: 12) {
                    HStack {
                        Label("Status", systemImage: "circle.fill")
                            .font(.caption)
                        Spacer()
                        Text(job.status.rawValue.capitalized)
                            .font(.caption)
                            .fontWeight(.semibold)
                            .foregroundColor(.blue)
                    }

                    HStack {
                        Label("Est. Duration", systemImage: "hourglass.end")
                            .font(.caption)
                        Spacer()
                        Text("\(job.estimatedDuration) min")
                            .font(.caption)
                            .fontWeight(.semibold)
                    }
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(12)

                Spacer()

                // Action Buttons
                VStack(spacing: 12) {
                    if isRunning {
                        Button(action: pauseTimer) {
                            Label("Pause", systemImage: "pause.fill")
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.orange)
                                .foregroundColor(.white)
                                .cornerRadius(8)
                        }
                    } else {
                        Button(action: startTimer) {
                            Label("Resume", systemImage: "play.fill")
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color.green)
                                .foregroundColor(.white)
                                .cornerRadius(8)
                        }
                    }

                    Button(action: { /* Show completion */ }) {
                        Label("Mark Complete", systemImage: "checkmark.circle.fill")
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(8)
                    }
                }
            }
            .padding()
        }
        .navigationTitle("Job Timer")
        .onAppear {
            startTimer()
        }
        .onDisappear {
            pauseTimer()
        }
    }

    private func startTimer() {
        guard !isRunning else { return }
        isRunning = true

        timerTask = Task {
            while isRunning {
                try? await Task.sleep(nanoseconds: 1_000_000_000)
                if isRunning {
                    elapsedSeconds += 1
                }
            }
        }
    }

    private func pauseTimer() {
        isRunning = false
        timerTask?.cancel()
    }
}

#Preview {
    JobTimerView(job: Job(
        id: "1",
        customerId: "c1",
        customerName: "John's HVAC",
        address: "123 Main St",
        latitude: 40.7128,
        longitude: -74.0060,
        jobType: "AC Repair",
        priority: 4,
        estimatedDuration: 45,
        status: .onSite,
        notes: nil,
        assignedAt: Date(),
        startedAt: Date(),
        completedAt: nil
    ))
    .environmentObject(JobService())
}
