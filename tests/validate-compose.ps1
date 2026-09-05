param(
    [ValidateSet('master', 'worker', 'all')]
    [string]$Target = 'all'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

function Test-ComposeFile {
    param([string]$Name)

    $composeFile = Join-Path $root "compose.$Name.yml"
    $environmentFile = Join-Path $root ".env.$Name.example"
    & docker compose --env-file $environmentFile -f $composeFile config --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Compose validation failed for $Name."
    }
}

if ($Target -eq 'all') {
    Test-ComposeFile 'master'
    Test-ComposeFile 'worker'
} else {
    Test-ComposeFile $Target
}
