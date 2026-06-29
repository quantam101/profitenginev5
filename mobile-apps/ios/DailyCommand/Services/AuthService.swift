import Foundation
import LocalAuthentication

class AuthService: NSObject, ObservableObject {
    @Published var isAuthenticated = false
    @Published var user: User?
    @Published var errorMessage: String?

    private let apiService = APIService()
    private let keychainService = KeychainService()

    override init() {
        super.init()
        checkAuthenticationStatus()
    }

    func login(email: String, password: String) async {
        do {
            let response = try await apiService.post(
                endpoint: "/api/auth/login",
                body: ["email": email, "password": password],
                responseType: LoginResponse.self
            )

            DispatchQueue.main.async {
                self.user = response.user
                self.isAuthenticated = true
                self.keychainService.save(token: response.token)
            }
        } catch {
            DispatchQueue.main.async {
                self.errorMessage = "Login failed: \(error.localizedDescription)"
            }
        }
    }

    func register(email: String, password: String, name: String) async {
        do {
            let response = try await apiService.post(
                endpoint: "/api/auth/register",
                body: [
                    "email": email,
                    "password": password,
                    "name": name
                ],
                responseType: LoginResponse.self
            )

            DispatchQueue.main.async {
                self.user = response.user
                self.isAuthenticated = true
                self.keychainService.save(token: response.token)
            }
        } catch {
            DispatchQueue.main.async {
                self.errorMessage = "Registration failed: \(error.localizedDescription)"
            }
        }
    }

    func biometricLogin() async {
        let context = LAContext()
        var error: NSError?

        guard context.canEvaluatePolicy(.deviceOwnerAuthenticationWithBiometrics, error: &error) else {
            DispatchQueue.main.async {
                self.errorMessage = "Biometric authentication not available"
            }
            return
        }

        do {
            let success = try await context.evaluatePolicy(
                .deviceOwnerAuthenticationWithBiometrics,
                localizedReason: "Login to Daily Command"
            )

            if success {
                if let token = keychainService.retrieveToken() {
                    DispatchQueue.main.async {
                        self.isAuthenticated = true
                    }
                }
            }
        } catch {
            DispatchQueue.main.async {
                self.errorMessage = "Biometric authentication failed"
            }
        }
    }

    func logout() {
        isAuthenticated = false
        user = nil
        keychainService.deleteToken()
    }

    private func checkAuthenticationStatus() {
        if let _ = keychainService.retrieveToken() {
            isAuthenticated = true
        }
    }
}

struct User: Codable {
    let id: String
    let email: String
    let name: String
    let phone: String
    let companyName: String
}

struct LoginResponse: Codable {
    let user: User
    let token: String
}
