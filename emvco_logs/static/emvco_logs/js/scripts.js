// New scripts.js for emvco_logs app matching astrex_html_logs style

let file = null;
let de032_counts = {};
let startTime;
let loadingTimerInterval;
let bm32NameMap = {};

let gifIndex = 0;
let gifs = [];

let loadingStartTime = null;
let loadingInterval = null;

// Load config mapping (bm32_config.json)
fetch('/media/astrex_html_logs/bm32_config.json')
  .then(res => res.json())
  .then(config => {
    bm32NameMap = {};
    Object.keys(config).forEach(brand => {
      const binMapping = config[brand];
      Object.keys(binMapping).forEach(bin => {
        bm32NameMap[bin] = { stationName: binMapping[bin], schemeName: brand };
      });
    });
  });

// Handle file selection
const xmlInput = document.getElementById('xmlLogFile');
if (xmlInput) {
  xmlInput.addEventListener('change', function(event) {
    file = event.target.files[0];
    document.getElementById('uploadedFileName').textContent = file ? file.name : '';

    if (file) {
      uploadFile();
    }
  });
}

// Upload File
// Upload File
function uploadFile() {
    if (!file || !file.name.endsWith('.xml')) {
      alert('Please select a valid XML file.');
      return;
    }
  
    startTime = new Date();
    showLoadingScreen();   // Show loading overlay immediately
    startLoadingTimer();   // Start showing elapsed time immediately
  
    const formData = new FormData();
    formData.append('file', file);
  
    fetch('/emvco_logs/upload/', {
      method: 'POST',
      body: formData,
      headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(res => res.json())
    .then(data => {
      hideLoadingScreen();             // Hide loading after success
      clearInterval(loadingTimerInterval);  // Stop the timer
  
      if (data.status === 'success') {
        loadSummary(data);   // Load the summary view
        document.getElementById('processingTimeContainer').style.display = 'block';
      } else {
        alert(data.error || 'Upload failed.');
      }
    })
    .catch(err => {
      hideLoadingScreen();             // Hide loading on failure too
      clearInterval(loadingTimerInterval);
      console.error(err);
      alert('Upload failed.');
    });
  }
  

  
// Load Summary
function loadSummary(uploadData) {
  fetch('/media/emvco_logs/unique_bm32_emvco.json')
    .then(res => res.json())
    .then(summary => {
      populateSummary(summary, uploadData);
      populateDE032Cards(summary.total_counts);
    })
    .catch(err => console.error('Summary load error:', err));
}

// Populate Summary Data
function populateSummary(summary, uploadData) {
  const container = document.getElementById('summaryContent');
  container.innerHTML = `
    <p><strong>Total Transactions:</strong> ${summary.total_de032_count}</p>
    <p><strong>Total PSP:</strong> ${summary.total_unique_count}</p>
    <p><strong>Start Time:</strong> ${uploadData.start_time}</p>
    <p><strong>End Time:</strong> ${uploadData.end_time}</p>
    <p><strong>Time Difference:</strong> ${uploadData.time_difference}</p>
  `;

  document.getElementById('downloadAllBtn').style.display = 'inline-block';
}

// Populate DE032 Cards
function populateDE032Cards(de032s) {
  const container = document.getElementById('summaryContainer');
  container.innerHTML = '';

  Object.entries(de032s).forEach(([de32, count]) => {
    const card = document.createElement('div');
    card.className = 'de32-card';

    const info = bm32NameMap[de32] || { stationName: 'Unknown', schemeName: 'Unknown' };

    card.innerHTML = `
      <h4>DE032: ${de32}</h4>
      <p><strong>PSP:</strong> ${info.stationName}</p>
      <p><strong>Scheme:</strong> ${info.schemeName}</p>
      <p><strong>Count:</strong> ${count}</p>
      <button class="button">⬇️ Download</button>
    `;

    const btn = card.querySelector('.button');
    btn.addEventListener('click', () => downloadFilteredFile(de32));

    container.appendChild(card);
  });
}

// Download Filtered Single File
function downloadFilteredFile(de32) {
  if (!file) return;

  showLoadingScreen();

  fetch('/emvco_logs/download_filtered_by_de032/', {
    method: 'POST',
    body: JSON.stringify({
      conditions: [de32],
      filename: file.name
    }),
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
      'Content-Type': 'application/json'
    }
  })
  .then(res => res.json())
  .then(result => {
    hideLoadingScreen();
    if (result.status === 'success') {
      const link = document.createElement('a');
      link.href = `/media/${result.filtered_file}`;
      link.download = result.filtered_file.split('/').pop();
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      alert(result.error || 'Download failed.');
    }
  })
  .catch(err => {
    hideLoadingScreen();
    console.error(err);
    alert('Download failed.');
  });
}

// Download All Filtered Files
const downloadAllBtn = document.getElementById('downloadAllBtn');
if (downloadAllBtn) {
  downloadAllBtn.addEventListener('click', function(event) {
    event.stopPropagation();
    if (!file) return;

    showLoadingScreen();

    fetch('/emvco_logs/download_filtered_by_de032/', {
      method: 'POST',
      body: JSON.stringify({
        conditions: [],
        filename: file.name
      }),
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json'
      }
    })
    .then(res => res.json())
    .then(result => {
      hideLoadingScreen();
      if (result.status === 'success') {
        const link = document.createElement('a');
        link.href = `/media/${result.filtered_file}`;
        link.download = result.filtered_file.split('/').pop();
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        alert(result.error || 'Download failed.');
      }
    })
    .catch(err => {
      hideLoadingScreen();
      console.error(err);
      alert('Download failed.');
    });
  });
}

// Loading Screen Functions
function showLoadingScreen() {
  document.getElementById('loadingOverlay').style.display = 'flex';
  startGifCycle();

  loadingStartTime = new Date();
  clearInterval(loadingInterval);
  loadingInterval = setInterval(updateElapsedTime, 1000);
}

function hideLoadingScreen() {
  document.getElementById('loadingOverlay').style.display = 'none';
  clearInterval(loadingInterval);
}

function startGifCycle() {
  const gifElements = document.querySelectorAll('#gifContainer .loading-gif');
  gifs = Array.from(gifElements);

  if (gifs.length === 0) return;

  gifs.forEach(gif => {
    gif.style.display = 'none';
    gif.style.opacity = 0;
  });

  gifIndex = 0;
  showNextGif();
}

function showNextGif() {
  gifs.forEach(gif => {
    gif.style.display = 'none';
    gif.style.opacity = 0;
  });

  const currentGif = gifs[gifIndex];
  currentGif.style.display = 'block';
  setTimeout(() => {
    currentGif.style.opacity = 1;
  }, 100);

  gifIndex = (gifIndex + 1) % gifs.length;
  setTimeout(showNextGif, 6000);
}

function startLoadingTimer() {
  loadingTimerInterval = setInterval(() => {
    const elapsedSeconds = Math.floor((new Date() - startTime) / 1000);
    document.getElementById('processingTime').textContent = `Elapsed Time: ${formatDuration(elapsedSeconds)}`;
  }, 1000);
}

function updateElapsedTime() {
  if (!loadingStartTime) return;

  const now = new Date();
  const elapsedMs = now - loadingStartTime;
  const elapsedSeconds = Math.floor(elapsedMs / 1000);

  const minutes = Math.floor(elapsedSeconds / 60);
  const seconds = elapsedSeconds % 60;

  document.getElementById('timer').textContent = `Elapsed time: ${minutes}m ${seconds}s`;
}

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}m ${secs}s`;
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
