# EDH Randomizer Test Setup and Runner
# Usage: .\run_tests.ps1 [-Setup] [-Headed] [-Slow]

param(
    [switch]$Setup,
    [switch]$Headed,
    [switch]$Slow,
    [switch]$Help
)

if ($Help) {
    Write-Host @"

EDH Randomizer Multiplayer Session Test Runner

Usage: .\run_tests.ps1 [options]

Options:
  -Setup      Install test dependencies (pytest, playwright)
  -Headed     Run tests with visible browser (watch the test)
  -Slow       Slow down test execution (500ms between actions)
  -Help       Show this help message

Examples:
  .\run_tests.ps1 -Setup              # First time setup
  .\run_tests.ps1                     # Run headless (fast)
  .\run_tests.ps1 -Headed             # Watch the test run
  .\run_tests.ps1 -Headed -Slow       # Watch in slow motion

Individual tests:
  pytest tests/test_multiplayer_session.py::test_full_multiplayer_session -v -s
  pytest tests/test_multiplayer_session.py::test_late_join_during_rolling -v -s

"@
    exit 0
}

if ($Setup) {
    Write-Host "`n============================================" -ForegroundColor Cyan
    Write-Host "🔧 Setting up test environment..." -ForegroundColor Cyan
    Write-Host "============================================`n" -ForegroundColor Cyan
    
    Write-Host "📦 Installing Python test dependencies..." -ForegroundColor Yellow
    pip install -r requirements-test.txt
    
    Write-Host "`n🌐 Installing Playwright browsers..." -ForegroundColor Yellow
    playwright install chromium
    
    Write-Host "`n✅ Setup complete! You can now run tests with:" -ForegroundColor Green
    Write-Host "   .\run_tests.ps1" -ForegroundColor White
    Write-Host "   .\run_tests.ps1 -Headed" -ForegroundColor White
    exit 0
}

# Build pytest command
$args = @(
    "pytest",
    "tests/test_multiplayer_session.py",
    "-v",
    "-s"
)

if ($Headed) {
    $args += "--headed"
    Write-Host "🖥️  Running tests with visible browser..." -ForegroundColor Yellow
} else {
    Write-Host "👻 Running tests in headless mode..." -ForegroundColor Yellow
}

if ($Slow) {
    $args += "--slowmo=500"
    Write-Host "🐌 Running with 500ms slowdown between actions..." -ForegroundColor Yellow
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "🧪 Running EDH Randomizer Multiplayer Tests" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Run the tests
& $args[0] $args[1..($args.Length-1)]

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "`n❌ Some tests failed. Check output above." -ForegroundColor Red
}

exit $LASTEXITCODE
