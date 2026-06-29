# ⚡ INSTALL JAVA - 5 MINUTES

## 🚀 QUICKEST PATH

### Step 1: Download Java
Visit: https://www.oracle.com/java/technologies/downloads/#java21

Click: **Windows x64 Installer** (for Windows)

### Step 2: Install
1. Run the installer
2. Click **Next** → **Next** → **Next** → **Finish**
3. Takes ~2 minutes

### Step 3: Verify Installation
```powershell
java -version
# Should show: java version "21" or similar
```

### Step 4: Set JAVA_HOME (if needed)
```powershell
# Check if JAVA_HOME is set
echo $env:JAVA_HOME

# If empty, add it (replace with your Java path)
[Environment]::SetEnvironmentVariable('JAVA_HOME', 'C:\Program Files\Java\jdk-21', 'User')

# Restart PowerShell and verify
java -version
```

---

## ✅ ALTERNATIVE: Use Android Studio's Built-in Java

If you have Android Studio installed:
```powershell
# Set JAVA_HOME to Android Studio's Java
[Environment]::SetEnvironmentVariable('JAVA_HOME', 'C:\Program Files\Android\Android Studio\jbr', 'User')

# Restart PowerShell
java -version
```

---

## ⏱️ TOTAL TIME
- Download: 2 minutes
- Install: 2 minutes
- Verify: 30 seconds
- **Total: ~5 minutes**

Then come back and run: `.\build.ps1`
