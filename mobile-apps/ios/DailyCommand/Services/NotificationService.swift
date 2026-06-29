import Foundation
import UserNotifications

class NotificationService {
    static let shared = NotificationService()

    func requestPermission(completion: @escaping (Bool) -> Void) {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, _ in
            DispatchQueue.main.async {
                completion(granted)
                if granted {
                    UIApplication.shared.registerForRemoteNotifications()
                }
            }
        }
    }

    func handleRemoteNotification(_ userInfo: [AnyHashable: Any]) {
        guard let aps = userInfo["aps"] as? [String: Any],
              let alert = aps["alert"] as? [String: Any],
              let title = alert["title"] as? String,
              let body = alert["body"] as? String else {
            return
        }

        let jobId = userInfo["jobId"] as? String ?? ""
        handleJobNotification(title: title, body: body, jobId: jobId)
    }

    func registerDeviceToken(_ token: Data) {
        let token = token.map { String(format: "%02.2hhx", $0) }.joined()
        sendTokenToBackend(token)
    }

    private func handleJobNotification(title: String, body: String, jobId: String) {
        DispatchQueue.main.async {
            // Handle job notification
            // This could trigger UI updates, navigate to job detail, etc.
            NotificationCenter.default.post(
                name: NSNotification.Name("JobNotificationReceived"),
                object: nil,
                userInfo: ["jobId": jobId, "title": title, "body": body]
            )
        }
    }

    private func sendTokenToBackend(_ token: String) {
        // TODO: Send APNs token to backend API
        // This should be called after user authenticates
    }
}
