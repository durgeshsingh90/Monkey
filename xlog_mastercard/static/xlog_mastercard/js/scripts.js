let timerInterval;
let gifIndex = 0;
let gifTimer;

document.getElementById('xlogFile').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (!file) {
        console.log('No file selected');
        return;
    }

    console.log('File selected:', file.name);

    if (!file.name.endsWith('.xlog')) {
        alert('Please upload a XLOG file only.');
        return;
    }

    document.getElementById('loadingOverlay').style.display = 'flex';
    startTimer();

    const formData = new FormData();
    formData.append('file', file);

    fetch('/xlog_mastercard/upload_file/', {
        method: 'POST',
        body: formData
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
    startGifSlideshow();

    timerInterval = setInterval(() => {
        const elapsedTime = Date.now() - startTime;
        const minutes = Math.floor(elapsedTime / 60000);
        const seconds = Math.floor((elapsedTime % 60000) / 1000);
        document.getElementById('timer').textContent = `Elapsed time: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
}

function stopTimer() {
    clearInterval(timerInterval);
    stopGifSlideshow();
    document.getElementById('timer').textContent = 'Elapsed time: 00:00';
}

function loadSummary(uploadData) {
    console.log('Loading summary data');

    fetch('/media/xlog_mastercard/unique_bm32_xlog.json')
    .then(response => response.json())
    .then(data => {
        console.log('Summary data:', data);
        displaySummary(data, uploadData);
    })
    .catch(error => {
        console.error('Error loading summary:', error);
    });
}

function displaySummary(data, uploadData) {
    const summaryContent = document.getElementById('summaryContent');
    const summaryContainer = document.getElementById('summaryContainer');
    summaryContent.innerHTML = '';
    summaryContainer.innerHTML = '';

    summaryContent.innerHTML = `
        <div>
            <p>Total Transactions: ${data.total_de032_count}</p>
            <p>Total Unique DE032: ${data.total_unique_count}</p>
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
        const card = document.createElement('div');
        card.className = 'de32-card';

        card.innerHTML = `
            <h4>DE032: ${de32}</h4>
            <p><strong>Count:</strong> ${count}</p>
            <button onclick="downloadFiltered('${de32}')" class="button">Download Filtered ZIP</button>
        `;
    
        summaryContainer.appendChild(card);
    }

    document.getElementById('downloadAllBtn').onclick = () => downloadAllFiltered(Object.keys(de32TotalCounts));
}


function showLoadingScreen() {
    document.getElementById('loadingOverlay').style.display = 'flex';
    startGifSlideshow();  // your existing function
    startTimer();         // your existing function
}

function hideLoadingScreen() {
    document.getElementById('loadingOverlay').style.display = 'none';
    stopTimer();          // your existing function
}

function downloadFiltered(de32) {
    const filename = document.getElementById('uploadedFileName').textContent;
    const payload = {
        conditions: [de32],
        filename: filename
    };

    showLoadingScreen();  // <-- Correct way

    fetch('/xlog_mastercard/download_filtered_by_de032/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingScreen();  // <-- Correct way

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
        hideLoadingScreen();  // <-- Correct way
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

    showLoadingScreen();  // <-- Correct way

    fetch('/xlog_mastercard/download_filtered_by_de032/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingScreen();  // <-- Correct way

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
        hideLoadingScreen();  // <-- Correct way
        console.error('Download error:', error);
        alert('Failed to download filtered results');
    });
}



function startGifSlideshow() {
    const gifs = document.querySelectorAll('#gifContainer .loading-gif');
    if (gifs.length === 0) return;

    gifs.forEach(gif => gif.style.display = 'none');
    gifs[gifIndex].style.display = 'block';

    gifTimer = setInterval(() => {
        gifs[gifIndex].style.display = 'none';
        gifIndex = (gifIndex + 1) % gifs.length;
        gifs[gifIndex].style.display = 'block';
    }, 6000);
}

function stopGifSlideshow() {
    clearInterval(gifTimer);
    gifIndex = 0;
}
