$ErrorActionPreference = 'Stop'
$localVoiceRoot = 'F:\aoe_4_temp\Community_civilization_pack_garrison_temp\tool-cache\local-voices-084'
if (-not (Test-Path -LiteralPath $localVoiceRoot)) { throw 'Local voice root unavailable' }
$env:UV_CACHE_DIR = "$localVoiceRoot\uv-cache"
$env:UV_PYTHON_INSTALL_DIR = "$localVoiceRoot\python"
$env:HF_HOME = "$localVoiceRoot\hf-cache"
$env:HUGGINGFACE_HUB_CACHE = "$localVoiceRoot\hf-cache\hub"
$env:TORCH_HOME = "$localVoiceRoot\torch-cache"
$env:TMP = "$localVoiceRoot\tmp"
$env:TEMP = $env:TMP
$env:XDG_CACHE_HOME = "$localVoiceRoot\cache"
$env:NUMBA_CACHE_DIR = "$localVoiceRoot\numba-cache"
$env:GRADIO_TEMP_DIR = "$localVoiceRoot\gradio-temp"
$env:UV_LINK_MODE = 'copy'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:HF_HUB_DISABLE_XET = '1'
$env:DO_NOT_TRACK = '1'
$env:GRADIO_ANALYTICS_ENABLED = 'False'
$env:PYTHONUTF8 = '1'
$env:PYTHONUNBUFFERED = '1'
$env:PYTHONPYCACHEPREFIX = "$localVoiceRoot\pycache"
$env:HF_TOKEN = $null
$env:HUGGING_FACE_HUB_TOKEN = $null
New-Item -ItemType Directory -Force -Path $env:TMP | Out-Null
