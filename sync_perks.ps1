# Sync perks.json from data/ to docs/data/
# Run this after editing data/perks.json

$source = "data\perks.json"
$dest = "docs\data\perks.json"

Write-Host "Syncing perks.json..." -ForegroundColor Cyan
Copy-Item $source $dest -Force
Write-Host "✓ Synced $source -> $dest" -ForegroundColor Green
