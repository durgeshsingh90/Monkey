// static/emvco_logs/js/scripts.js

let file = null;
let de032_counts = {};
let startTime;
let loadingTimerInterval;

document.getElementById('xmlLogFile').addEventListener('change', function(e) {
    file = e.target.files[0];
    document.getElementById('uploadedFileName').textContent = file ? file.name : '';

    if (file) {
        uploadFile();
    }
});

function uploadFile() {
    if (!file || !file.name.endsWith('.xml')) {
        alert('Please select a valid XML file.');
        return;
    }

    startTime = new Date();
    startLoadingScreen();

    const formData = new FormData();
    formData.append('file', file);

    fetch('/emvco_logs/upload_log/', {
        method: 'POST',
        body: formData
    }).then(res => res.json())
      .then(data => {
        stopLoadingScreen();

        if (data.status === 'success') {
            const container = document.getElementById('de032Container');
            container.innerHTML = '';

            de032_counts = data.de032_counts;
            const totalCount = data.total_de032_count;

            const summaryDetails = document.getElementById('summaryDetails');
            summaryDetails.innerHTML = `
                <p>Total Unique DE032: ${Object.keys(de032_counts).length}</p>
                <p>Total Occurrences: ${totalCount}</p>
            `;

            Object.entries(de032_counts).forEach(([key, count]) => {
                const box = document.createElement('div');
                box.className = 'de032-box';
                box.innerHTML = `
                    <div class="de032-header">DE032: ${key}</div>
                    <div class="count">Count: ${count}</div>
                    <button class="download-btn">Download</button>
                `;

                const btn = box.querySelector('.download-btn');
                btn.addEventListener('click', () => downloadFiltered(key));

                container.appendChild(box);
            });
        } else {
            alert(data.message);
        }
    })
    .catch(err => {
        stopLoadingScreen();
        console.error(err);
        alert('Upload failed.');
    });
}

function downloadFiltered(de032) {
    const dlForm = new FormData();
    dlForm.append('de032', de032);
    dlForm.append('filename', file.name);

    startLoadingScreen();

    fetch('/emvco_logs/download_filtered/', {
        method: 'POST',
        body: dlForm
    }).then(res => res.json())
      .then(result => {
        stopLoadingScreen();
        if (result.status === 'success') {
            const link = document.createElement('a');
            link.href = `/media/${result.filtered_file}`;
            link.download = result.filtered_file.split('/').pop();
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else {
            alert(result.message);
        }
    })
    .catch(err => {
        stopLoadingScreen();
        console.error(err);
        alert('Download failed.');
    });
}

function startLoadingScreen() {
    document.getElementById('loadingScreen').style.display = 'block';
    startTimer();
}

function stopLoadingScreen() {
    document.getElementById('loadingScreen').style.display = 'none';
    clearInterval(loadingTimerInterval);
}

function startTimer() {
    loadingTimerInterval = setInterval(() => {
        const elapsedSeconds = Math.floor((new Date() - startTime) / 1000);
        document.getElementById('loadingTimer').textContent = `Loading: ${elapsedSeconds}s`;
    }, 1000);
}
