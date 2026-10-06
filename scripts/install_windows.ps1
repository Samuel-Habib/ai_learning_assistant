# ==============================================================================
# Adaptive Study Assistant - Windows Installer (PowerShell)
# ==============================================================================
Write-Host "🪟 Setting up Adaptive Study Assistant for Windows..." -ForegroundColor Cyan

# Check Python
$pythonInstalled = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonInstalled) {
    $python3Installed = Get-Command python3 -ErrorAction SilentlyContinue
    if (-not $python3Installed) {
        Write-Host "⚠️ Python 3 not found. Installing via winget..." -ForegroundColor Yellow
        winget install -e --id Python.Python.3.12
    }
} else {
    Write-Host "✓ Python is installed." -ForegroundColor Green
}

# Install pypdf fallback for PDF extraction on Windows
Write-Host "📦 Ensuring pypdf is installed for PDF course materials..." -ForegroundColor Cyan
python -m pip install --quiet pypdf

# Setup .env if not exists
$scriptDir = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $scriptDir ".env"
$envExamplePath = Join-Path $scriptDir ".env.example"

if (-not (Test-Path $envPath)) {
    if (Test-Path $envExamplePath) {
        Copy-Item $envExamplePath $envPath
        Write-Host "📝 Created .env configuration file from template." -ForegroundColor Green
        Write-Host "👉 Open .env and add your GEMINI_API_KEY, OPENAI_API_KEY, or GROQ_API_KEY." -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ .env file already exists." -ForegroundColor Green
}

Write-Host "`n🎉 Windows Installation Complete!" -ForegroundColor Green
Write-Host "To start studying, run in PowerShell:" -ForegroundColor White
Write-Host "  python learn" -ForegroundColor Yellow
Write-Host "Or on Windows Subsystem for Linux (WSL):" -ForegroundColor White
Write-Host "  ./learn" -ForegroundColor Yellow
