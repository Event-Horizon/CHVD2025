$ErrorActionPreference = "Stop";

$workingDir = (Split-Path -Parent $MyInvocation.MyCommand.Definition);
$venvDIR = Join-Path -Path $workingDir -ChildPath ".venv";
$requirementsFile = Join-Path -Path $workingDir -ChildPath "requirements.txt";
$chvdScript = Join-Path -Path $workingDir -ChildPath "VideoDownload.py";
$pythonExe = Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source;
$python3Exe = Get-Command python3.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source;
$venvPYTHON = Join-Path -Path $venvDIR -ChildPath "Scripts\python.exe";

Write-Host "Prepping Clone Hero Video Downloader...";
try {
    if (-not (Test-Path $requirementsFile)) {
        throw "requirements.txt not found. Make sure it's in the same directory as this script.";
    }
    if (-not (Test-Path $chvdScript)) {
        throw "VideoDownload.py not found. Make sure it's in the same directory as this script.";
    }
    if ($python3Exe) {
        $pythonExe = $python3Exe
    } elseif ($pythonExe) {
        $pythonExe = $pythonExe
    }else{
        throw "Python (or python3) not found. Please install Python 3.x and ensure it's in your PATH.";
    }
    if (-not (Test-Path $venvDIR)) {
        Write-Host "Creating virtual environment...";
        & $pythonExe -m venv $venvDIR | Out-Null;
    }else{
        Write-Host "Virtual environment already exists..." 
        if (-not (Test-Path $venvPYTHON)) {
            throw "Virtual environment's Python executable not found after creation.";
        }
    }
    Write-Host "Installing dependencies...";
    & $venvPYTHON -m pip install -r $requirementsFile;
    Write-Host "Running VideoDownload.py..."
    & $venvPYTHON $chvdScript;
} catch {
    Write-Error "Run failed: $($_.Exception.Message)";
    Read-Host -Prompt "Press any key to exit..." | Out-Null;
    exit 1;
}
Write-Host "Process completed successfully."
Read-Host -Prompt "Press any key to exit..." | Out-Null;