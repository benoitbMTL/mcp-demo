#requires -Version 5.1

$ErrorActionPreference = "Stop"

$MCP_URL = "http://mcp-xperts.labsec.ca/mcp"
$ACCEPT_HEADER = "application/json, text/event-stream"

function Show-Section {
    param([string]$Title)

    Write-Host ""
    Write-Host "============================================================"
    Write-Host $Title
    Write-Host "============================================================"
}

function Show-Request {
    param(
        [string]$Method,
        [hashtable]$Headers,
        [string]$Body
    )

    $uri = [System.Uri]$MCP_URL

    Write-Host "POST $($uri.AbsolutePath) HTTP/1.1"
    Write-Host "Host: $($uri.Authority)"

    foreach ($key in $Headers.Keys) {
        Write-Host ("{0}: {1}" -f $key, $Headers[$key])
    }

    Write-Host ""
    Write-Host $Body
}

function Get-SessionId {
    $initBody = @{
        jsonrpc = "2.0"
        id      = 0
        method  = "initialize"
        params  = @{
            protocolVersion = "2025-11-05"
            capabilities    = @{}
            clientInfo      = @{
                name    = "powershell"
                version = "1.0"
            }
        }
    } | ConvertTo-Json -Compress

    $headers = @{
        "Content-Type" = "application/json"
        "Accept"       = $ACCEPT_HEADER
    }

    Show-Section "STEP 2 - JSON-RPC initialize request"
    Show-Request -Method "POST" -Headers $headers -Body $initBody

    $response = Invoke-WebRequest `
        -Uri $MCP_URL `
        -Method POST `
        -Headers $headers `
        -Body $initBody `
        -UseBasicParsing

    foreach ($key in $response.Headers.Keys) {
        if ($key -ieq "Mcp-Session-Id") {
            return [string]$response.Headers[$key]
        }
    }

    throw "Mcp-Session-Id header not found."
}

function Extract-JsonFromResponse {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        throw "Response body is empty."
    }

    if ($Text -match '(?m)^data:\s*') {
        $lines = $Text -split "`r?`n"
        $jsonLines = @()

        foreach ($line in $lines) {
            if ($line -match '^data:\s?(.*)$') {
                $jsonLines += $Matches[1]
            }
        }

        if ($jsonLines.Count -eq 0) {
            throw "No JSON payload found in SSE response."
        }

        return ($jsonLines -join "`n").Trim()
    }

    return $Text.Trim()
}

function Get-ToolNames {
    param([string]$JsonText)

    $obj = $JsonText | ConvertFrom-Json

    if ($obj.error) {
        throw $obj.error.message
    }

    if ($obj.result -and $obj.result.tools) {
        return $obj.result.tools | ForEach-Object { $_.name }
    }

    if ($obj.tools) {
        return $obj.tools | ForEach-Object { $_.name }
    }

    throw "Tools list not found in response."
}

Show-Section "STEP 1 - MCP endpoint"
Write-Host "MCP URL: $MCP_URL"
Write-Host "Accept: $ACCEPT_HEADER"

$sessionId = Get-SessionId

Show-Section "STEP 3 - Session established"
Write-Host "Mcp-Session-Id: $sessionId"

$toolsBody = @{
    jsonrpc = "2.0"
    id      = 1
    method  = "tools/list"
} | ConvertTo-Json -Compress

$toolsHeaders = @{
    "Content-Type"   = "application/json"
    "Accept"         = $ACCEPT_HEADER
    "Mcp-Session-Id" = $sessionId
}

Show-Section "STEP 4 - JSON-RPC tools/list request"
Show-Request -Method "POST" -Headers $toolsHeaders -Body $toolsBody

$response = Invoke-WebRequest `
    -Uri $MCP_URL `
    -Method POST `
    -Headers $toolsHeaders `
    -Body $toolsBody `
    -UseBasicParsing

$json = Extract-JsonFromResponse $response.Content
$tools = Get-ToolNames $json

Show-Section "STEP 5 - Tool names"
$tools
