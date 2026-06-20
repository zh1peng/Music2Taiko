$ErrorActionPreference = "Stop"

$sourceRoot = "E:\music2taiko\tmp_motif_redlead_render"
$targetRoot = "E:\OpenTaiko Hub\OpenTaiko\Songs\L2 Custom Charts\02 Children & Folk"
$packages = @(
    "yt-test-baby-shark",
    "dl-jingle-bells-jingle-bells",
    "dl-xiao-mao-lv-chart",
    "y2-xiao-xing-chart",
    "y2-liang-hu-chart"
)

if (!(Test-Path $sourceRoot)) {
    throw "Missing source root: $sourceRoot"
}
if (!(Test-Path $targetRoot)) {
    throw "Missing OpenTaiko target root: $targetRoot"
}

foreach ($package in $packages) {
    $source = Join-Path $sourceRoot $package
    $target = Join-Path $targetRoot $package
    if (!(Test-Path $source)) {
        throw "Missing generated package: $source"
    }
    if (!(Test-Path $target)) {
        New-Item -ItemType Directory -Force -Path $target | Out-Null
    }

    Copy-Item -Path (Join-Path $source "*") -Destination $target -Recurse -Force
    Write-Host "Overwrote $package"
}

Write-Host "OpenTaiko packages updated."
