#Requires -Version 5.1
<#
    deploy.ps1 - ship the backend to Render.

    Builds the Docker image (linux/amd64), verifies no .env leaked into it, pushes
    :latest and :<git-sha> to Docker Hub (tabletopsoftware/pathfinder_char_creator-web),
    then triggers a Render redeploy via the hook stored in .env (RENDER_DEPLOY_HOOK_URL).

    Prerequisites (one-time):
      - Docker Desktop running
      - `docker login` as tabletopsoftware
      - RENDER_DEPLOY_HOOK_URL=... present in .env  (gitignored)

    Usage:
      ./deploy.ps1            # build + push + trigger Render
      ./deploy.ps1 -NoDeploy  # build + push only (skip the Render trigger)
      ./deploy.ps1 -NoCache   # force a clean rebuild
#>
[CmdletBinding()]
param(
    [switch]$NoDeploy,
    [switch]$NoCache
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false   # we check $LASTEXITCODE ourselves

$Image = 'tabletopsoftware/pathfinder_char_creator-web'
$Root  = $PSScriptRoot
$Svc   = 'srv-d2r7kqh5pdvs738v18s0'
Set-Location $Root

function Fail($msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

# 1. Docker daemon reachable?
docker info 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "Docker isn't running. Start Docker Desktop and retry." }

# 2. Tags
$Sha = (& git rev-parse --short HEAD 2>$null)
if (-not $Sha) { $Sha = 'manual' }
$TagLatest = "${Image}:latest"
$TagSha    = "${Image}:$Sha"

# 3. Build (Render runs linux/amd64)
Write-Host "==> Building $TagLatest (+ :$Sha) for linux/amd64" -ForegroundColor Cyan
$buildArgs = @('build', '--platform', 'linux/amd64', '-t', $TagLatest, '-t', $TagSha)
if ($NoCache) { $buildArgs += '--no-cache' }
$buildArgs += '.'
& docker $buildArgs
if ($LASTEXITCODE -ne 0) { Fail "docker build failed." }

# 4. Safety gate: the image must NOT contain .env
Write-Host "==> Verifying the image contains no .env" -ForegroundColor Cyan
$check = & docker run --rm $TagLatest sh -c 'if [ -f /app/.env ]; then echo LEAK; else echo CLEAN; fi'
if ($check -notmatch 'CLEAN') { Fail "'.env' found inside the image - aborting push. Check .dockerignore." }
Write-Host "    CLEAN - no .env in image." -ForegroundColor Green

# 5. Push both tags
Write-Host "==> Pushing to Docker Hub" -ForegroundColor Cyan
& docker push $TagLatest; if ($LASTEXITCODE -ne 0) { Fail "docker push :latest failed. Run 'docker login' as tabletopsoftware." }
& docker push $TagSha;    if ($LASTEXITCODE -ne 0) { Fail "docker push :$Sha failed." }

# 6. Trigger Render
if ($NoDeploy) { Write-Host "==> -NoDeploy set; image pushed, Render NOT triggered." -ForegroundColor Yellow; exit 0 }
$line = Get-Content "$Root\.env" -ErrorAction SilentlyContinue | Where-Object { $_ -like 'RENDER_DEPLOY_HOOK_URL=*' } | Select-Object -First 1
if (-not $line) { Fail "RENDER_DEPLOY_HOOK_URL missing from .env - image is pushed, but Render was not triggered." }
$hookUrl = $line.Substring('RENDER_DEPLOY_HOOK_URL='.Length).Trim()

Write-Host "==> Triggering Render redeploy" -ForegroundColor Cyan
try { $resp = Invoke-RestMethod -Method Post -Uri $hookUrl } catch { Fail "Render trigger failed: $($_.Exception.Message)" }
Write-Host "    Render deploy queued: $($resp | ConvertTo-Json -Compress)" -ForegroundColor Green
Write-Host ""
Write-Host "Shipped ${Image}:latest ($Sha) -> Render $Svc" -ForegroundColor Green
Write-Host "Watch: https://dashboard.render.com/web/$Svc" -ForegroundColor Green
