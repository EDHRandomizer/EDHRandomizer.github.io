# Sync powerups.json from data/ to docs/data/
# Run this after editing data/powerups.json

$source = "data\powerups.json"
$dest = "docs\data\powerups.json"

Write-Host "Syncing powerups.json..." -ForegroundColor Cyan
Copy-Item $source $dest -Force
Write-Host "✓ Synced $source -> $dest" -ForegroundColor Green
