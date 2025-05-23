// Toggle individual buttons
['updateBtn', 'echoBtn', 'incrBtn'].forEach(id => {
  const btn = document.getElementById(id);
  if (btn) {
    btn.addEventListener('click', () => {
      btn.classList.toggle('active');
    });
  }
});

// Exclusive group (only one can be active at a time)
const exclusiveButtons = ['dev77', 'paypal77', 'novate', 'test77', 'cert77', 'netscaler'];
exclusiveButtons.forEach(id => {
  const btn = document.getElementById(id);
  if (btn) {
    btn.addEventListener('click', () => {
      exclusiveButtons.forEach(otherId => {
        const otherBtn = document.getElementById(otherId);
        if (otherBtn) otherBtn.classList.remove('active');
      });
      btn.classList.add('active');
    });
  }
});

// SEND button sends selected test cases
document.getElementById('sendBtn')?.addEventListener('click', () => {
  const selected = Array.from(selectedTestCases).map(tc => {
    try {
      return JSON.parse(tc);
    } catch {
      return null;
    }
  }).filter(Boolean);

  if (selected.length === 0) {
    alert("No test cases selected.");
    return;
  }

  fetch('/api/send/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({ testcases: selected })
  })
    .then(res => res.ok ? res.json() : Promise.reject('Failed'))
    .then(data => {
      alert("✅ Sent successfully!");
    })
    .catch(err => {
      console.error("❌ Send failed:", err);
      alert("❌ Failed to send test cases.");
    });
});

// CSRF helper
function getCSRFToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}


// Add File Modal
const addFileModal = document.getElementById('addFileModal');
document.getElementById('addFileBtn').addEventListener('click', () => {
  document.getElementById('newFilename').value = '';
  addFileModal.classList.remove('hidden');
});

document.getElementById('cancelAddFile').addEventListener('click', () => {
  addFileModal.classList.add('hidden');
});

document.getElementById('confirmAddFile').addEventListener('click', () => {
  const filename = document.getElementById('newFilename').value.trim();
  const rootname = document.getElementById('newRootName').value.trim();

  if (!filename.endsWith('.json')) {
    alert("Filename must end with .json");
    return;
  }

  if (!rootname) {
    alert("Please enter a root test suite name.");
    return;
  }

  const formData = new FormData();
  formData.append('filename', filename);
  formData.append('rootname', rootname);

  fetch('/junglewire/create_testcase_file/', {
    method: 'POST',
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'created') {
        alert('File created!');
        location.reload();
      } else {
        alert(data.error || 'Error creating file.');
      }
    })
    .catch(err => {
      alert("Failed to create file");
      console.error(err);
    });
});



// Upload File
document.getElementById('uploadFileInput').addEventListener('change', function () {
  const file = this.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  fetch('/junglewire/upload_testcase_file/', {
    method: 'POST',
    body: formData
  }).then(res => {
    if (res.status === 409) {
      if (confirm("File already exists. Overwrite?")) {
        formData.append('overwrite', 'true');
        return fetch('/junglewire/upload_testcase_file/', { method: 'POST', body: formData });
      }
    }
    return res;
  }).then(res => res.json())
    .then(data => {
      if (data.status === 'uploaded') {
        alert('Upload successful');
        location.reload();
      } else {
        alert(data.error || 'Error uploading');
      }
    });
});

// Download Button
document.getElementById('downloadBtn').addEventListener('click', () => {
  const selectedFiles = new Set();

  for (const tc of selectedTestCases) {
    try {
      const parsed = JSON.parse(tc);
      if (parsed.__source) {
        selectedFiles.add(parsed.__source);
      }
    } catch {}
  }

  if (!selectedFiles.size) {
    alert("No test case selected.");
    return;
  }

  selectedFiles.forEach(file => {
    const link = document.createElement('a');
    link.href = `/media/junglewire/testcase/${file}.json`;
    link.download = `${file}.json`;
    document.body.appendChild(link); // needed for Firefox
    link.click();
    document.body.removeChild(link);
  });
});
