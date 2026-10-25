param([ValidateSet('base','cuda')][string]$Stage = 'base')
. "$PSScriptRoot\local_env.ps1"
$uv = 'C:\Users\RS\.local\bin\uv.exe'
$python = "$localVoiceRoot\venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw 'Create isolated F: Python environment first' }
if ($Stage -eq 'base') {
    & $uv --quiet pip install --python $python "$localVoiceRoot\VieNeu-TTS" 'transformers==4.57.6'
} else {
    $torchWheel = "$localVoiceRoot\downloads\torch-2.8.0+cu128-cp311-cp311-win_amd64.whl"
    $expected = '34c55443aafd31046a7963b63d30bc3b628ee4a704f826796c865fdfd05bb596'
    if ((Get-FileHash -LiteralPath $torchWheel -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) { throw 'PyTorch download hash mismatch or incomplete download' }
    & $uv --quiet pip install --python $python $torchWheel 'torchaudio==2.8.0' --index-url https://download.pytorch.org/whl/cu128
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $uv --quiet pip install --python $python accelerate
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $uv pip freeze --python $python | Out-File -Encoding utf8 "$localVoiceRoot\requirements-$Stage.lock.txt"
