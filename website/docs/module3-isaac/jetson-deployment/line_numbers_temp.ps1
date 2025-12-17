$lines = Get-Content "C:\Users\Admin\Desktop\BOOK\website\docs\module3-isaac\jetson-deployment\optimization.mdx"
for ($i = 0; $i -lt $lines.Length; $i++) {
    Write-Output "$($i + 1): $($lines[$i])"
}