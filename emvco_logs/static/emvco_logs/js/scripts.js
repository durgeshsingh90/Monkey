let bm32Config = {};
let timerInterval;

document.getElementById('xmlLogFile').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (!file) {
        console.log('No file selected');
        return;
    }

    console.log('File selected:', file.name);

    if (!file.name.endsWith('.xml')) {
        alert('Please upload an XML file only.');
        return;
    }

    document.getElementById('loadingOverlay').style.display = 'block';
    startTimer();

    const formData = new FormData();
    formData.append('file', file);

    fetch('/emvco_logs/upload/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        console.log('Response received from server:', data);

        document.getElementById('loadingOverlay').style.display = 'none';
        stopTimer();

        if (data.status === 'success') {
            document.getElementById('uploadedFileName').textContent = data.filename;
            document.getElementById('processingTime').textContent = data.processing_time;
            document.getElementById('processingTimeContainer').style.display = 'block';
            loadSummary(data);
        } else {
            alert('Upload failed: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        document.getElementById('loadingOverlay').style.display = 'none';
        stopTimer();
        console.error('Upload error:', error);
        alert('Upload failed');
    });
});

function startTimer() {
    let startTime = Date.now();
    startGifSlideshow(); // Start GIF rotation

    timerInterval = setInterval(() => {
        const elapsedTime = Date.now() - startTime;
        const minutes = Math.floor(elapsedTime / 60000);
        const seconds = Math.floor((elapsedTime % 60000) / 1000);
        document.getElementById('timer').textContent = `Elapsed time: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
}


function stopTimer() {
    clearInterval(timerInterval);
    stopGifSlideshow(); // Stop GIF rotation
    document.getElementById('timer').textContent = 'Elapsed time: 00:00';
}


function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (const cookie of cookies) {
            const trimmedCookie = cookie.trim();
            if (trimmedCookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(trimmedCookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getBm32Info(bm32) {
    for (const [scheme, stations] of Object.entries(bm32Config)) {
        if (stations[bm32]) {
            return {
                stationName: stations[bm32],
                schemeName: scheme
            };
        }
    }
    return null;
}

function displaySummary(data, uploadData) {
    const summaryContent = document.getElementById('summaryContent');
    const summaryContainer = document.getElementById('summaryContainer');
    summaryContent.innerHTML = '';
    summaryContainer.innerHTML = '';

    summaryContent.innerHTML = `
        <div>
            <p>Total Transactions: ${data.total_de032_count}</p>
            <p>Total PSP: ${data.total_unique_count}</p>
            <p>Start Time: ${uploadData.start_time}</p>
            <p>End Time: ${uploadData.end_time}</p>
            <p>Time Difference: ${uploadData.time_difference}</p>
        </div>
    `;

    const de32TotalCounts = data.total_counts;

    if (Object.keys(de32TotalCounts).length > 0) {
        document.getElementById('downloadAllBtn').style.display = 'block';
    }

    for (const [de32, count] of Object.entries(de32TotalCounts)) {
        const info = getBm32Info(de32);
        const card = document.createElement('div');
        card.className = 'de32-card';

        card.innerHTML = `
        <h4>DE032: ${de32}</h4>
        <p><strong>PSP:</strong> ${info ? info.stationName : 'Unknown'}</p>
        <p><strong>Scheme:</strong> ${info ? info.schemeName : 'Unknown'}</p>
        <p><strong>Count:</strong> ${count}</p>
        <button onclick="downloadFiltered('${de32}')" class="button">Download Filtered ZIP</button>
    `;
    
        summaryContainer.appendChild(card);
    }

    document.getElementById('downloadAllBtn').onclick = () => downloadAllFiltered(Object.keys(de32TotalCounts));
}

function loadSummary(uploadData) {
    console.log('Loading summary data');

    fetch('/media/emvco_logs/unique_bm32_emvco.json')
    .then(response => response.json())
    .then(data => {
        console.log('Summary data:', data);

        return fetch('/media/astrex_html_logs/bm32_config.json')
            .then(response => response.json())
            .then(configData => {
                bm32Config = configData;
                displaySummary(data, uploadData);
            });
    })
    .catch(error => {
        console.error('Error loading summary:', error);
    });
}

function downloadFiltered(de32) {
    console.log(`Downloading filtered results for DE032: ${de32}`);
    const filename = document.getElementById('uploadedFileName').textContent;
    const payload = {
        conditions: [de32],
        filename: filename
    };

    fetch('/emvco_logs/download_filtered_by_de032/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const downloadUrl = '/media/' + data.filtered_file;
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = downloadUrl.split('/').pop();
            document.body.appendChild(a);
            a.click();
            a.remove();
        } else {
            alert('Failed to download: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Download error:', error);
        alert('Failed to download filtered results');
    });
}

function downloadAllFiltered(de32List) {
    const filename = document.getElementById('uploadedFileName').textContent;
    const payload = {
        conditions: de32List,
        filename: filename
    };

    fetch('/emvco_logs/download_filtered_by_de032/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const downloadUrl = '/media/' + data.filtered_file;
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = downloadUrl.split('/').pop();
            document.body.appendChild(a);
            a.click();
            a.remove();
        } else {
            alert('Failed to download: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Download error:', error);
        alert('Failed to download filtered results');
    });
}
let gifIndex = 0;
let gifTimer;

function startGifSlideshow() {
    const gifs = document.querySelectorAll('#gifContainer .loading-gif');
    if (gifs.length === 0) return;

    // Hide all GIFs initially
    gifs.forEach(gif => gif.style.display = 'none');

    // Show the first GIF
    gifs[gifIndex].style.display = 'block';

    // Start rotating
    gifTimer = setInterval(() => {
        gifs[gifIndex].style.display = 'none'; // Hide current
        gifIndex = (gifIndex + 1) % gifs.length; // Next index
        gifs[gifIndex].style.display = 'block'; // Show next
    }, 6000); // 6 seconds
}

function stopGifSlideshow() {
    clearInterval(gifTimer);
    gifIndex = 0;
}
