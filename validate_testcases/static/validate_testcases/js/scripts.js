let excelFile = null, logFile = null;

document.getElementById('excelFile').addEventListener('change', (e) => {
  excelFile = e.target.files[0];
  tryUpload();
});
document.getElementById('logFile').addEventListener('change', (e) => {
  logFile = e.target.files[0];
  tryUpload();
});

function tryUpload() {
  const status = document.getElementById('status');
  const spinner = document.getElementById('spinner');

  if (!excelFile || !logFile) return;

  status.innerText = '⏳ Uploading and processing...';
  spinner.classList.remove('hidden');

  const formData = new FormData();
  formData.append('excel', excelFile);
  formData.append('log', logFile);

  fetch('/validate_testcases/upload_and_compare/', {
    method: 'POST',
    body: formData
  }).then(res => res.json()).then(data => {
    spinner.classList.add('hidden');
    if (data.status === 'success') {
      renderTabs(data.excel_preview);
      document.getElementById('comparisonContainer').classList.remove('hidden');
      document.getElementById('comparisonPreview').innerText = data.comparison_preview;
      document.getElementById('logDownload').href = data.download_log;
      status.innerText = '✅ Comparison complete. See result below.';
    } else {
      status.innerText = '❌ ' + data.message;
    }
  }).catch(() => {
    spinner.classList.add('hidden');
    status.innerText = '❌ Upload failed.';
  });
}

function renderTabs(previews) {
  const tabs = document.getElementById('tabs');
  const preview = document.getElementById('preview');
  tabs.innerHTML = '';
  preview.innerHTML = '';

  Object.entries(previews).forEach(([sheet, html], i) => {
    const btn = document.createElement('button');
    btn.textContent = sheet;
    btn.className = 'px-3 py-1 border rounded bg-gray-100';
    btn.onclick = () => {
      preview.innerHTML = html;
    };
    tabs.appendChild(btn);
    if (i === 0) preview.innerHTML = html;
  });
}

// Go to Top
const goTopBtn = document.getElementById('goTopBtn');
window.addEventListener('scroll', () => {
  goTopBtn.classList.toggle('hidden', window.scrollY < window.innerHeight * 2);
});
goTopBtn.addEventListener('click', () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
});
