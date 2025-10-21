Write-Host "=== Testing Multithreaded Server ===" -ForegroundColor Green
Write-Host "Launching 5 concurrent client requests..." -ForegroundColor Yellow

$jobs = @()
$jobs += Start-Job -ScriptBlock { cd "C:\Users\crist\Desktop\University\Year3\PR\Lab2"; py client.py localhost 8001 /index.html }
$jobs += Start-Job -ScriptBlock { cd "C:\Users\crist\Desktop\University\Year3\PR\Lab2"; py client.py localhost 8001 /sample.pdf }
$jobs += Start-Job -ScriptBlock { cd "C:\Users\crist\Desktop\University\Year3\PR\Lab2"; py client.py localhost 8001 /library.png }
$jobs += Start-Job -ScriptBlock { cd "C:\Users\crist\Desktop\University\Year3\PR\Lab2"; py client.py localhost 8001 /books/ }
$jobs += Start-Job -ScriptBlock { cd "C:\Users\crist\Desktop\University\Year3\PR\Lab2"; py client.py localhost 8001 / }

Write-Host "All clients started! Waiting for completion..." -ForegroundColor Cyan

$jobs | Wait-Job | Out-Null

Write-Host "`n=== Results ===" -ForegroundColor Green
$jobs | ForEach-Object { 
    Write-Host "`n--- Job $($_.Id) ---" -ForegroundColor Yellow
    Receive-Job $_
}

$jobs | Remove-Job

Write-Host "`n=== Test Complete! ===" -ForegroundColor Green
Write-Host "Check the server logs to see all requests were handled concurrently!" -ForegroundColor Cyan
