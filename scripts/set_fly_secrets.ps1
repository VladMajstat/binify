# set_fly_secrets.ps1 — PowerShell helper. Заповни змінні і запусти після `fly auth login`
param(
    [Parameter(Mandatory=$true)]
    [string]$AppName
)

if (-not $AppName) {
    Write-Host "Usage: .\set_fly_secrets.ps1 -AppName <app-name>"
    exit 1
}

$secrets = @(
    @{Name='DJANGO_SECRET_KEY'; Value='your_django_secret'},
    @{Name='DATABASE_URL'; Value='postgresql://user:password@host:5432/dbname?sslmode=require'},
    @{Name='REDIS_HOST'; Value='your-redis-host'},
    @{Name='REDIS_PORT'; Value='your-redis-port'},
    @{Name='REDIS_PASSWORD'; Value='your-redis-password'},
    @{Name='AWS_ACCESS_KEY_ID'; Value='your_r2_key'},
    @{Name='AWS_SECRET_ACCESS_KEY'; Value='your_r2_secret'},
    @{Name='AWS_STORAGE_BUCKET_NAME'; Value='binify-bucket'},
    @{Name='AWS_S3_ENDPOINT_URL'; Value='https://your-account.r2.cloudflarestorage.com'},
    @{Name='AWS_S3_CUSTOM_DOMAIN'; Value='binify-bucket.your-account.r2.cloudflarestorage.com'},
    @{Name='ALLOWED_HOSTS'; Value="$($AppName).fly.dev"},
    @{Name='CSRF_TRUSTED_ORIGINS'; Value="https://$($AppName).fly.dev"}
)

$cmd = 'fly secrets set '
$parts = @()
foreach ($s in $secrets) {
    $parts += "${($s.Name)}=\"${($s.Value)}\""
}
$full = $cmd + ($parts -join ' ')
Write-Host "Running: $full"
Invoke-Expression $full
Write-Host "Secrets set for app: $AppName"
