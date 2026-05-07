$terraform = "C:\Tools\Terraform\terraform.exe"

if (-not (Test-Path $terraform)) {
    Write-Error "Terraform no esta instalado en $terraform"
    exit 1
}

$varsFile = Join-Path $PSScriptRoot "terraform.tfvars"
if (-not (Test-Path $varsFile)) {
    Write-Error "Falta terraform.tfvars en $PSScriptRoot"
    exit 1
}

$varsContent = Get-Content $varsFile -Raw
$missingPlaceholders = @(
    "replace-with-account-id",
    "replace-with-zone-id",
    "example.com"
) | Where-Object { $varsContent -match [regex]::Escape($_) }

if ($missingPlaceholders.Count -gt 0) {
    Write-Warning "Todavia hay placeholders en terraform.tfvars: $($missingPlaceholders -join ', ')"
}

if (-not $env:CLOUDFLARE_API_TOKEN) {
    Write-Warning "Falta la variable de entorno CLOUDFLARE_API_TOKEN en esta sesion."
}

& $terraform version
