from __future__ import annotations

import base64
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path


def capture_screenshot() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    temp_dir = Path(tempfile.gettempdir())
    output_path = temp_dir / f"telegram-pc-bot-screenshot-{timestamp}.png"

    command = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "Add-Type -AssemblyName System.Drawing; "
        "$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen; "
        "$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height; "
        "$graphics = [System.Drawing.Graphics]::FromImage($bitmap); "
        "$graphics.CopyFromScreen($bounds.Left, $bounds.Top, 0, 0, $bitmap.Size); "
        f"$bitmap.Save('{output_path}', [System.Drawing.Imaging.ImageFormat]::Png); "
        "$graphics.Dispose(); "
        "$bitmap.Dispose();"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not output_path.exists():
        raise RuntimeError(result.stderr.strip() or "Failed to capture screenshot")
    return output_path


def get_memory_summary() -> str:
    command = (
        "$os = Get-CimInstance Win32_OperatingSystem; "
        "$total = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2); "
        "$free = [math]::Round($os.FreePhysicalMemory / 1MB, 2); "
        "$used = [math]::Round($total - $free, 2); "
        "$percent = if ($total -eq 0) { 0 } else { [math]::Round(($used / $total) * 100, 1) }; "
        "$top = Get-Process | Sort-Object WS -Descending | Select-Object -First 5 ProcessName,@{Name='MemoryMB';Expression={[math]::Round($_.WS / 1MB, 1)}}; "
        "$lines = @(); "
        "$lines += ('RAM: {0} GB usados de {1} GB ({2}%)' -f $used, $total, $percent); "
        "$lines += ('Disponivel: {0} GB' -f $free); "
        "$lines += 'Top processos por memoria:'; "
        "foreach ($proc in $top) { $lines += ('- {0}: {1} MB' -f $proc.ProcessName, $proc.MemoryMB) }; "
        "$lines -join [Environment]::NewLine"
    )
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError(result.stderr.strip() or "Failed to read memory usage")
    return result.stdout.strip()
