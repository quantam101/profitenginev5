import SwiftUI
import MapKit

struct JobDetailView: View {
    let job: Job
    @EnvironmentObject var jobService: JobService
    @State private var showStartConfirmation = false
    @State private var showCompleteSheet = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                // Header
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(job.customerName)
                            .font(.title2)
                            .fontWeight(.bold)
                        HStack {
                            Image(systemName: "mappin.circle.fill")
                                .foregroundColor(.blue)
                            Text(job.address)
                                .font(.caption)
                                .foregroundColor(.gray)
                        }
                    }
                    Spacer()
                    StatusBadge(status: job.status)
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(12)

                // Details
                VStack(alignment: .leading, spacing: 12) {
                    DetailRow(label: "Service Type", value: job.jobType)
                    DetailRow(label: "Priority", value: "\(job.priority)/5")
                    DetailRow(label: "Est. Duration", value: "\(job.estimatedDuration) min")
                    DetailRow(label: "Assigned", value: formatDate(job.assignedAt))
                }
                .padding()
                .background(Color(.systemGray6))
                .cornerRadius(12)

                // Map Preview
                ZStack(alignment: .topTrailing) {
                    MapView(latitude: job.latitude, longitude: job.longitude)
                        .frame(height: 200)
                        .cornerRadius(12)
                        .clipped()

                    Button(action: { openMaps() }) {
                        Image(systemName: "location.circle.fill")
                            .font(.system(size: 32))
                            .foregroundColor(.blue)
                            .padding()
                    }
                }

                // Notes
                if let notes = job.notes, !notes.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Notes")
                            .font(.headline)
                        Text(notes)
                            .font(.caption)
                            .foregroundColor(.gray)
                            .lineLimit(3)
                    }
                    .padding()
                    .background(Color(.systemGray6))
                    .cornerRadius(12)
                }

                Spacer()

                // Action Buttons
                VStack(spacing: 12) {
                    if job.status == .pending {
                        Button(action: { showStartConfirmation = true }) {
                            HStack {
                                Image(systemName: "play.fill")
                                Text("Start Job")
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.blue)
                            .foregroundColor(.white)
                            .cornerRadius(8)
                        }
                    }

                    if job.status == .onSite || job.status == .enRoute {
                        Button(action: { showCompleteSheet = true }) {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                Text("Complete Job")
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.green)
                            .foregroundColor(.white)
                            .cornerRadius(8)
                        }
                    }

                    if job.status == .onSite {
                        Button(action: { updateStatus(.enRoute) }) {
                            Text("Heading Back")
                                .frame(maxWidth: .infinity)
                                .padding()
                                .background(Color(.systemGray5))
                                .foregroundColor(.primary)
                                .cornerRadius(8)
                        }
                    }
                }
            }
            .padding()
        }
        .navigationTitle("Job Details")
        .confirmationDialog("Start Job?", isPresented: $showStartConfirmation) {
            Button("Start") {
                Task {
                    await jobService.startJob(job)
                }
            }
        } message: {
            Text("Begin work on \(job.customerName)'s job at \(job.address)?")
        }
        .sheet(isPresented: $showCompleteSheet) {
            JobCompletionView(job: job)
                .environmentObject(jobService)
        }
    }

    private func updateStatus(_ status: JobStatus) {
        Task {
            await jobService.updateJobStatus(job, status: status)
        }
    }

    private func openMaps() {
        let url = "https://maps.apple.com/?q=\(job.latitude),\(job.longitude)"
        if let mapURL = URL(string: url) {
            UIApplication.shared.open(mapURL)
        }
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.timeStyle = .short
        formatter.dateStyle = .short
        return formatter.string(from: date)
    }
}

struct DetailRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .font(.caption)
                .foregroundColor(.gray)
            Spacer()
            Text(value)
                .font(.caption)
                .fontWeight(.semibold)
        }
    }
}

struct MapView: UIViewRepresentable {
    let latitude: Double
    let longitude: Double

    func makeUIView(context: Context) -> MKMapView {
        let map = MKMapView()
        let region = MKCoordinateRegion(
            center: CLLocationCoordinate2D(latitude: latitude, longitude: longitude),
            span: MKCoordinateSpan(latitudeDelta: 0.05, longitudeDelta: 0.05)
        )
        map.setRegion(region, animated: true)

        let annotation = MKPointAnnotation()
        annotation.coordinate = CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
        map.addAnnotation(annotation)

        return map
    }

    func updateUIView(_ uiView: MKMapView, context: Context) {}
}

#Preview {
    JobDetailView(job: Job(
        id: "1",
        customerId: "c1",
        customerName: "John's HVAC",
        address: "123 Main St, Springfield",
        latitude: 40.7128,
        longitude: -74.0060,
        jobType: "AC Repair",
        priority: 4,
        estimatedDuration: 45,
        status: .pending,
        notes: "Fix cooling system",
        assignedAt: Date(),
        startedAt: nil,
        completedAt: nil
    ))
    .environmentObject(JobService())
}
