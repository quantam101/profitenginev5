import SwiftUI
import PhotosUI

struct JobCompletionView: View {
    let job: Job
    @EnvironmentObject var jobService: JobService
    @Environment(\.dismiss) var dismiss

    @State private var notes = ""
    @State private var selectedPhotos: [PhotosPickerItem] = []
    @State private var photoData: [Data] = []
    @State private var isSubmitting = false

    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Job Details")) {
                    Text(job.customerName)
                    Text(job.address)
                        .font(.caption)
                        .foregroundColor(.gray)
                }

                Section(header: Text("Completion Notes")) {
                    TextEditor(text: $notes)
                        .frame(minHeight: 100)
                        .placeholder(when: notes.isEmpty) {
                            Text("Describe work completed...")
                                .foregroundColor(.gray)
                        }
                }

                Section(header: Text("Photos")) {
                    PhotosPicker(
                        selection: $selectedPhotos,
                        matching: .images,
                        photoLibrary: .shared()
                    ) {
                        HStack {
                            Image(systemName: "camera.fill")
                            Text("Add Photos")
                        }
                    }
                    .onChange(of: selectedPhotos) { newItems in
                        Task {
                            photoData.removeAll()
                            for item in newItems {
                                if let data = try? await item.loadTransferable(type: Data.self) {
                                    photoData.append(data)
                                }
                            }
                        }
                    }

                    if !photoData.isEmpty {
                        ScrollView(.horizontal) {
                            HStack(spacing: 8) {
                                ForEach(0..<photoData.count, id: \.self) { index in
                                    ZStack(alignment: .topTrailing) {
                                        if let uiImage = UIImage(data: photoData[index]) {
                                            Image(uiImage: uiImage)
                                                .resizable()
                                                .scaledToFill()
                                                .frame(width: 100, height: 100)
                                                .clipped()
                                                .cornerRadius(8)
                                        }
                                        Button(action: {
                                            photoData.remove(at: index)
                                            selectedPhotos.remove(at: index)
                                        }) {
                                            Image(systemName: "xmark.circle.fill")
                                                .foregroundColor(.red)
                                        }
                                        .padding(4)
                                    }
                                }
                            }
                        }
                        .padding(.vertical, 8)
                    }
                }

                Section {
                    Button(action: submitCompletion) {
                        if isSubmitting {
                            ProgressView()
                                .frame(maxWidth: .infinity)
                        } else {
                            HStack {
                                Image(systemName: "checkmark.circle.fill")
                                Text("Complete Job")
                            }
                            .frame(maxWidth: .infinity)
                        }
                    }
                    .disabled(isSubmitting || notes.isEmpty)
                    .foregroundColor(.green)
                }
            }
            .navigationTitle("Complete Job")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
            }
        }
    }

    private func submitCompletion() {
        isSubmitting = true
        Task {
            await jobService.completeJob(job, photos: photoData, notes: notes)
            dismiss()
        }
    }
}

extension View {
    func placeholder<Content: View>(when shouldShow: Bool, alignment: Alignment = .leading, @ViewBuilder placeholder: () -> Content) -> some View {
        ZStack(alignment: alignment) {
            placeholder().opacity(shouldShow ? 1 : 0)
            self
        }
    }
}

#Preview {
    JobCompletionView(job: Job(
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
