#Requires -RunAsAdministrator
<#
  One-time fix for LAN access to News Router dev servers on Windows.
  Sets Wi-Fi/Ethernet to Private and opens firewall for dev ports + Node/Python.

  Run from an elevated terminal:
    npm run fix-lan

  Or double-click after right-click → Run as administrator.
#>
$ErrorActionPreference = 'Stop'

Write-Host ''
Write-Host '  News Router — LAN access fix' -ForegroundColor Cyan
Write-Host ''

# 1. Set active networks to Private (Public blocks most inbound traffic)
$profiles = Get-NetConnectionProfile | Where-Object { $_.NetworkCategory -ne 'Private' }
if ($profiles) {
	foreach ($p in $profiles) {
		Write-Host "  Setting $($p.InterfaceAlias) to Private (was $($p.NetworkCategory))..."
		Set-NetConnectionProfile -InterfaceIndex $p.InterfaceIndex -NetworkCategory Private
	}
} else {
	Write-Host '  Network profile already Private.'
}

# 2. Port rules for dev ranges
$portRules = @(
	@{ Name = 'News Router Dev (Web)'; Port = '5173-5272' },
	@{ Name = 'News Router Dev (API)'; Port = '8000-8099' },
	@{ Name = 'News Router Dev (ntfy)'; Port = '2586' }
)

foreach ($rule in $portRules) {
	netsh advfirewall firewall delete rule name="$($rule.Name)" 2>$null | Out-Null
	netsh advfirewall firewall add rule `
		name="$($rule.Name)" `
		dir=in action=allow protocol=TCP localport=$($rule.Port) `
		enable=yes profile=private,public | Out-Null
	Write-Host "  + $($rule.Name)  TCP $($rule.Port)"
}

# 3. Program rules — more reliable than ports alone on Public profile
$programs = @(
	@{ Name = 'News Router Dev (Node.js)'; Path = (Get-Command node -ErrorAction SilentlyContinue).Source },
	@{ Name = 'News Router Dev (Python)'; Path = (Get-Command python -ErrorAction SilentlyContinue).Source }
)

foreach ($prog in $programs) {
	if (-not $prog.Path) { continue }
	netsh advfirewall firewall delete rule name="$($prog.Name)" 2>$null | Out-Null
	netsh advfirewall firewall add rule `
		name="$($prog.Name)" `
		dir=in action=allow program="$($prog.Path)" `
		enable=yes profile=private,public | Out-Null
	Write-Host "  + $($prog.Name)  $($prog.Path)"
}

# 4. Show LAN URLs
$ips = Get-NetIPAddress -AddressFamily IPv4 |
	Where-Object {
		$_.IPAddress -notmatch '^(127\.|169\.254\.)' -and
		$_.PrefixOrigin -ne 'WellKnown'
	} |
	Select-Object -ExpandProperty IPAddress

Write-Host ''
Write-Host '  Done. Restart npm run start:dev, then open on your phone:' -ForegroundColor Green
foreach ($ip in $ips) {
	Write-Host "    http://${ip}:5173"
}
Write-Host ''
Write-Host '  Keep this PC awake and the dev server running while testing.' -ForegroundColor DarkGray
Write-Host ''
