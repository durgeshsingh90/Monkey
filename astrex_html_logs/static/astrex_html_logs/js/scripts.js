let file = null;
let de032_counts = {};
let startTime;
let loadingTimerInterval;
let loadingTimeout;
let bm32NameMap = {};

let gifIndex = 0;
let gifs = [];

let loadingStartTime = null;
let loadingInterval = null;

// Load config mapping
fetch('/astrex_html_logs/load_config/')
  .then(res => res.json())
  .then(config => {
    bm32NameMap = {};

    // Flatten nested structure
    Object.keys(config).forEach(brand => {
      const binMapping = config[brand];
      Object.keys(binMapping).forEach(bin => {
        bm32NameMap[bin] = binMapping[bin];
      });
    });
  });

// Handle file selection
document.getElementById('htmlLogFile').addEventListener('change', function(e) {
  file = e.target.files[0];
  document.getElementById('uploadedFileName').textContent = file ? file.name : '';

  if (file) {
    document.getElementById('copyFileNameBtn').style.display = 'inline-block';
    uploadFile();
  } else {
    document.getElementById('copyFileNameBtn').style.display = 'none';
  }
});

// Upload the selected file
function uploadFile() {
  if (!file || !file.name.endsWith('.html')) {
    alert('Please select a valid HTML file.');
    return;
  }

  startTime = new Date();
  startLoadingTimer();
  loadingTimeout = setTimeout(showLoadingScreen, 1000);

  const formData = new FormData();
  formData.append('file', file);

  fetch('/astrex_html_logs/upload_log/', {
    method: 'POST',
    body: formData
  }).then(res => res.json())
  .then(data => {
    clearTimeout(loadingTimeout);
    hideLoadingScreen();
    clearInterval(loadingTimerInterval);

    if (data.status === 'success') {
      populateSummary(data);
      populateDE032Cards(data.de032_counts);

      document.getElementById('scriptRunDuration').style.display = 'block';
    } else {
      alert(data.message);
    }
  })
  .catch(err => {
    clearTimeout(loadingTimeout);
    hideLoadingScreen();
    clearInterval(loadingTimerInterval);
    console.error(err);
    alert('Upload failed.');
  });
}

// Populate Summary
function populateSummary(data) {
  const summaryDetails = document.getElementById('summaryDetails');
  
  const uniqueDE032Count = Object.keys(data.de032_counts || {}).length; // ✅ count unique DE032s

  summaryDetails.innerHTML = `
    <p><strong>Total Transactions:</strong> ${data.total_DE032_count}</p>
    <p><strong>Total PSP:</strong> ${uniqueDE032Count}</p>
    <p><strong>Start Log Time:</strong> ${data.start_log_time}</p>
    <p><strong>End Log Time:</strong> ${data.end_log_time}</p>
    <p><strong>Log Duration:</strong> ${calculateDuration(data.start_log_time, data.end_log_time)}</p>
  `;

  document.getElementById('scriptRunDuration').textContent =
    `Script Run Duration: ${calculateExecutionDuration(Math.floor((new Date() - startTime) / 1000))}`;

  document.getElementById('downloadAllBtn').style.display = 'inline-block';
}

// Create DE032 cards
function populateDE032Cards(de032s) {
  const container = document.getElementById('de032Container');
  container.innerHTML = '';

  Object.entries(de032s).forEach(([key, count]) => {
    const card = document.createElement('div');
    card.className = 'de32-card';
    const displayName = bm32NameMap[key] ? ` (${bm32NameMap[key]})` : '';

    card.innerHTML = `
      <h4>DE032: ${key}${displayName}</h4>
      <div class="count">Count: ${count}</div>
      <button class="button">⬇️ Download</button>
    `;

    const btn = card.querySelector('.button');
    btn.addEventListener('click', () => downloadFilteredFile(key));

    container.appendChild(card);
  });
}

// Download filtered DE032
function downloadFilteredFile(de032Key) {
  const formData = new FormData();
  formData.append('de032', de032Key);
  formData.append('filename', file.name);

  showLoadingScreen();

  fetch('/astrex_html_logs/download_filtered/', {
    method: 'POST',
    body: formData
  }).then(res => res.json())
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
      alert(result.message);
    }
  }).catch(err => {
    hideLoadingScreen();
    console.error(err);
    alert('Download failed.');
  });
}

// Download all filtered files
document.getElementById('downloadAllBtn').addEventListener('click', function(event) {
  event.stopPropagation();
  showLoadingScreen();

  const formData = new FormData();
  formData.append('filename', file.name);

  fetch('/astrex_html_logs/zip_filtered_files/', {
    method: 'POST',
    body: formData
  }).then(res => res.json())
  .then(result => {
    hideLoadingScreen();
    if (result.status === 'success') {
      const link = document.createElement('a');
      link.href = `/media/${result.zip_file}`;
      link.download = result.zip_file.split('/').pop();
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      alert(result.message);
    }
  }).catch(err => {
    hideLoadingScreen();
    console.error(err);
    alert('Download failed.');
  });
});

// Copy filename
document.getElementById('copyFileNameBtn').addEventListener('click', function () {
  const text = document.getElementById('uploadedFileName').textContent;
  navigator.clipboard.writeText(text)
    .then(() => {
      document.getElementById('copyFileNameBtn').textContent = '✅';
      setTimeout(() => {
        document.getElementById('copyFileNameBtn').textContent = '📋';
      }, 1500);
    })
    .catch(err => {
      alert('Failed to copy filename');
      console.error(err);
    });
});

// Loading screen functions
function showLoadingScreen() {
  document.getElementById('loadingScreen').style.display = 'flex';
  startGifCycle();

  loadingStartTime = new Date();
  clearInterval(loadingInterval);
  loadingInterval = setInterval(updateElapsedTime, 1000);
}

function hideLoadingScreen() {
  document.getElementById('loadingScreen').style.display = 'none';
  clearInterval(loadingInterval);
}

// Cycle GIFs
function startGifCycle() {
  const gifElements = document.querySelectorAll('.loading-gif');
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

// Timer for main script execution
function startLoadingTimer() {
  loadingTimerInterval = setInterval(() => {
    const elapsedSeconds = Math.floor((new Date() - startTime) / 1000);
    document.getElementById('scriptRunDuration').textContent =
      `Script Run Duration: ${calculateExecutionDuration(elapsedSeconds)}`;
  }, 1000);
}

// Update elapsed time on loading screen
function updateElapsedTime() {
  if (!loadingStartTime) return;

  const now = new Date();
  const elapsedMs = now - loadingStartTime;
  const elapsedSeconds = Math.floor(elapsedMs / 1000);

  const minutes = Math.floor(elapsedSeconds / 60);
  const seconds = elapsedSeconds % 60;

  document.getElementById('elapsedTime').textContent = `Elapsed Time: ${minutes}m ${seconds}s`;
}

// Utility time formatters
function calculateDuration(start, end) {
  const startTime = new Date(start);
  const endTime = new Date(end);
  const duration = endTime - startTime;

  const hours = Math.floor(duration / (1000 * 60 * 60));
  const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((duration % (1000 * 60)) / 1000);

  return `${hours}h ${minutes}m ${seconds}s`;
}

function calculateExecutionDuration(executionTime) {
  const hours = Math.floor(executionTime / 3600);
  const minutes = Math.floor((executionTime % 3600) / 60);
  const seconds = executionTime % 60;
  return `${hours}h ${minutes}m ${seconds}s`;
}
