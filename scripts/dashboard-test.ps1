# Tests the login and dashboard endpoints of the LeadFlow backend.
# Run from the project folder:  .\scripts\dashboard-test.ps1
# The password is typed into a hidden prompt and is never printed or saved.

$base = "http://localhost:8000"

$email = Read-Host "Admin email"
$sec = Read-Host "Admin password" -AsSecureString
$plain = [System.Net.NetworkCredential]::new("", $sec).Password
Write-Host ("Password length typed: " + $plain.Length)

$body = @{ email = $email; password = $plain } | ConvertTo-Json
try {
    $login = Invoke-RestMethod -Method Post -Uri "$base/auth/login" -ContentType "application/json" -Body $body
} catch {
    Write-Host ("Login failed with status " + $_.Exception.Response.StatusCode.value__)
    return
}
$plain = $null
$body = $null
$h = @{ Authorization = "Bearer $($login.access_token)" }
Write-Host "Login OK, token type:" $login.token_type

Write-Host ""
Write-Host "--- Who am I ---"
Invoke-RestMethod -Uri "$base/auth/me" -Headers $h | Format-Table email, full_name, role

Write-Host "--- Pending drafts ---"
$list = @(Invoke-RestMethod -Uri "$base/dashboard/drafts?status=pending" -Headers $h)
if ($list.Count -eq 0 -or -not $list[0].draft_id) {
    Write-Host "No pending drafts."
} else {
    $list | Format-Table lead_name, company, category, priority, status
    $id = $list[0].draft_id
    Write-Host "--- First pending draft in detail ---"
    Invoke-RestMethod -Uri "$base/dashboard/drafts/$id" -Headers $h |
        Select-Object lead_name, lead_status, category, priority, summary, subject |
        Format-List
}

Write-Host "--- Protection checks (both must say 401) ---"
try {
    Invoke-RestMethod -Uri "$base/dashboard/drafts" | Out-Null
    Write-Host "No token: NOT PROTECTED"
} catch {
    Write-Host ("No token: " + $_.Exception.Response.StatusCode.value__)
}
try {
    Invoke-RestMethod -Uri "$base/dashboard/drafts" -Headers @{ "x-api-key" = "wrong" } | Out-Null
    Write-Host "Wrong api key: NOT PROTECTED"
} catch {
    Write-Host ("Wrong api key: " + $_.Exception.Response.StatusCode.value__)
}

if ($list.Count -gt 0 -and $list[0].draft_id) {
    Write-Host ""
    $answer = Read-Host "Test editing the first pending draft? This overwrites its text. (y/N)"
    if ($answer -eq "y") {
        $edit = @{
            subject = "Thank you for your inquiry"
            body    = "Hello, thank you for reaching out. A member of our team will contact you shortly."
        } | ConvertTo-Json
        Invoke-RestMethod -Method Patch -Uri "$base/dashboard/drafts/$id" -Headers $h -ContentType "application/json" -Body $edit |
            Format-Table subject, status
    }
}
Write-Host "Done."

