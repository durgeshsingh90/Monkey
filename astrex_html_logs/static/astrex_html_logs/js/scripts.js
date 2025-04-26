let file = null;
let de032_counts = {};
let startTime;
let loadingTimerInterval;
let loadingTimeout;
let bm32NameMap = {};

// Load config mapping (bm32 name mappings)
fetch('/astrex_html_logs/load_config/')
  .then(res => res.json())
  .then(config => {
    bm32NameMap = {};

    // Flatten nested brand -> bin -> name structure
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
    document.getElementById('copyFileNameBtn').style.display = 'inline-block'; // Show copy icon
    uploadFile();
  } else {
    document.getElementById('copyFileNameBtn').style.display = 'none'; // Hide copy icon
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

      document.getElementById('scriptRunDuration').style.display = 'block'; // ✅ Show script duration AFTER processing
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

// Fill Summary Details
function populateSummary(data) {
  const summaryDetails = document.getElementById('summaryDetails');
  summaryDetails.innerHTML = `
    <p><strong>Total DE032 Count:</strong> ${data.total_DE032_count}</p>
    <p><strong>Total Transactions:</strong> ${data.total_txn}</p>
    <p><strong>Start Log Time:</strong> ${data.start_log_time}</p>
    <p><strong>End Log Time:</strong> ${data.end_log_time}</p>
    <p><strong>Log Duration:</strong> ${calculateDuration(data.start_log_time, data.end_log_time)}</p>
  `;

  document.getElementById('scriptRunDuration').textContent =
    `Script Run Duration: ${calculateExecutionDuration(Math.floor((new Date() - startTime) / 1000))}`;

  document.getElementById('downloadAllBtn').style.display = 'inline-block'; // Enable download all
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

// Download filtered by DE032
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

// Download all filtered
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

// Copy filename to clipboard
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

// Show and hide loading screen
function showLoadingScreen() {
  document.getElementById('loadingScreen').style.display = 'flex';
}

function hideLoadingScreen() {
  document.getElementById('loadingScreen').style.display = 'none';
}

// Timer utilities
function startLoadingTimer() {
  loadingTimerInterval = setInterval(() => {
    const elapsedSeconds = Math.floor((new Date() - startTime) / 1000);
    document.getElementById('scriptRunDuration').textContent =
      `Script Run Duration: ${calculateExecutionDuration(elapsedSeconds)}`;
  }, 1000);
}

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

let gifIndex = 0;
let gifs = [];

function startGifCycle() {
  const gifElements = document.querySelectorAll('.loading-gif');
  gifs = Array.from(gifElements);

  if (gifs.length === 0) return;

  // Hide all gifs initially
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
  }, 100); // Fade in

  gifIndex = (gifIndex + 1) % gifs.length;

  setTimeout(showNextGif, 6000); // Change GIF every 2 seconds
}

// When showing loading screen, start gif cycling
function showLoadingScreen() {
  document.getElementById('loadingScreen').style.display = 'flex';
  startGifCycle();
}

// Hide loading screen normally
function hideLoadingScreen() {
  document.getElementById('loadingScreen').style.display = 'none';
}
