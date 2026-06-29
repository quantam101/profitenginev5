import SwiftUI

@main
struct DailyCommandApp: App {
    @StateObject private var authService = AuthService()
    @StateObject private var jobService = JobService()

    var body: some Scene {
        WindowGroup {
            if authService.isAuthenticated {
                MainTabView()
                    .environmentObject(authService)
                    .environmentObject(jobService)
            } else {
                LoginView()
                    .environmentObject(authService)
            }
        }
    }
}
