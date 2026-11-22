# 포스터 pptx를 실제 PowerPoint로 PDF로 내보낸다(글꼴 포함). 실행: pwsh -File to_pdf.ps1 [파일 이름]
param([string]$name = "포스터_v1_한글")
$dir = Split-Path -Parent $PSScriptRoot
$pptx = Join-Path $dir "$name.pptx"
$pdf = Join-Path $dir "$name.pdf"
$alreadyOpen = Get-Process POWERPNT -ErrorAction SilentlyContinue
$app = New-Object -ComObject PowerPoint.Application
try {
    $p = $app.Presentations.Open($pptx, -1, 0, 0)
    $p.SaveCopyAs($pdf, 32)
    $p.Close()
    Write-Output "PDF 저장: $pdf"
}
finally {
    if (-not $alreadyOpen) { $app.Quit() }
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
