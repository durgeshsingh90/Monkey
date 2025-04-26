document.getElementById('xmlLogFile').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.xml')) {
        alert('Please upload an XML file only.');
        return;
    }

    document.getElementById('loadingOverlay').style.display = 'block';

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
        document.getElementById('loadingOverlay').style.display = 'none';

        if (data.status === 'success') {
            document.getElementById('uploadedFileName').textContent = data.filename;
            loadSummary();
        } else {
            alert('Upload failed: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        document.getElementById('loadingOverlay').style.display = 'none';
        console.error('Upload error:', error);
        alert('Upload failed');
    });
});

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

function loadSummary() {
    fetch('/media/emvco_logs/unique_bm32_emvco.json')
    .then(response => response.json())
    .then(data => {
        const summaryContainer = document.getElementById('summaryContainer');
        summaryContainer.innerHTML = '';

        const de32List = Object.keys(data.total_counts || {});
        
        if (de32List.length > 0) {
            document.getElementById('downloadAllBtn').style.display = 'block';
        }

        de32List.forEach(de32 => {
            const card = document.createElement('div');
            card.className = 'de32-card';
            card.innerHTML = `
                <h4>DE032: ${de32}</h4>
                <button onclick="downloadFiltered('${de32}')">Download Filtered ZIP</button>
            `;
            summaryContainer.appendChild(card);
        });

        document.getElementById('downloadAllBtn').onclick = () => downloadAllFiltered(de32List);
    })
    .catch(error => {
        console.error('Error loading summary:', error);
    });
}

function downloadFiltered(de32) {
    const payload = { conditions: [de32] };

    fetch('/emvco_logs/download_filtered_by_de032/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `filtered_${de32}.zip`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(error => {
        console.error('Download error:', error);
        alert('Failed to download');
    });
}

function downloadAllFiltered(de32List) {
    const payload = { conditions: de32List };

    fetch('/emvco_logs/download_filtered_by_de032/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'filtered_all_de032.zip';
        document.body.appendChild(a);
        a.click();
        a.remove();
    })
    .catch(error => {
        console.error('Download error:', error);
        alert('Failed to download');
    });
}
