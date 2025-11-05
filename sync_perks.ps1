# Sync perks.json from data/ to docs/data/ and api/
# Run this after editing data/perks.json

$source = "data\perks.json"
$dest_docs = "docs\data\perks.json"
$dest_api = "api\perks.json"

Write-Host "Syncing perks.json..." -ForegroundColor Cyan
Copy-Item $source $dest_docs -Force
Copy-Item $source $dest_api -Force
Write-Host "✓ Synced:" -ForegroundColor Green
Write-Host "  $source" -ForegroundColor Gray
Write-Host "  -> $dest_docs" -ForegroundColor Gray
Write-Host "  -> $dest_api" -ForegroundColor Gray
