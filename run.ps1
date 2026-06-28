# News Router — start the full site with one command.
# Usage:  .\run.ps1          -> npm run start:dev
#         .\run.ps1 -Docker  -> npm run start:prod

param([switch]$Docker)

Set-Location $PSScriptRoot

if ($Docker) {
    npm run start:prod
} else {
    npm run start:dev
}
