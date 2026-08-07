Invoke-RestMethod -Uri "http://localhost:8000/update_image_url" `
    -Method POST `
    -Headers @{ "Content-Type" = "application/json" } `
    -Body '{ "image_url": "https://console.runpod.io/" }'
