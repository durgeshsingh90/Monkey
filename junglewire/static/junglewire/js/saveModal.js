document.getElementById('openSaveModalBtn').addEventListener('click', () => {
  const saveModal = document.getElementById('saveModal');
  const modalTitle = document.getElementById('modalTitle');
  const saveIdEl = document.getElementById('saveId');
  const saveNameEl = document.getElementById('saveName');
  const fileSelect = document.getElementById('fileSelect');
  const rootSelect = document.getElementById('rootSelect');

  if (!saveModal || !modalTitle || !saveIdEl || !saveNameEl || !fileSelect || !rootSelect) {
    console.error("Missing modal input elements.");
    return;
  }

  saveModal.classList.remove('hidden');
  modalTitle.textContent = loadedTestcase ? "Update Test Case" : "Add New Test Case";

  fileSelect.innerHTML = '<option value="">Loading...</option>';
  rootSelect.innerHTML = '<option value="">Select a file first</option>';

  fetch('/junglewire/list_testcase_files/')
    .then(res => res.ok ? res.json() : Promise.reject("Failed to fetch files"))
    .then(files => {
      fileSelect.innerHTML = '<option value="">Select File</option>';
      files.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f;
        opt.textContent = f;
        fileSelect.appendChild(opt);
      });
    });

  if (loadedTestcase) {
    saveIdEl.value = loadedTestcase.id || '';
    saveNameEl.value = loadedTestcase.name || '';
  } else {
    saveIdEl.value = '';
    saveNameEl.value = '';
  }
});

document.getElementById('cancelSaveBtn').addEventListener('click', () => {
  const saveModal = document.getElementById('saveModal');
  if (saveModal) {
    saveModal.classList.add('hidden');
  }
});

document.getElementById('fileSelect').addEventListener('change', () => {
  const fileSelect = document.getElementById('fileSelect');
  const rootSelect = document.getElementById('rootSelect');
  const selectedFile = fileSelect?.value;

  if (!fileSelect || !rootSelect || !selectedFile) return;
  rootSelect.innerHTML = '<option value="">Loading roots...</option>';

  fetch(`/junglewire/load_testcase/${selectedFile}`)
    .then(res => res.ok ? res.json() : Promise.reject("Failed to load file"))
    .then(data => {
      const suites = Array.isArray(data) ? data : [data];
      rootSelect.innerHTML = '<option value="">Select Root Suite</option>';
      suites.forEach(suite => {
        const opt = document.createElement('option');
        opt.value = suite.name;
        opt.textContent = suite.name;
        rootSelect.appendChild(opt);
      });

      rootSelect.addEventListener('change', () => {
        const selectedRoot = rootSelect.value;
        if (!selectedRoot) return;

        const matchedSuite = suites.find(s => s.name === selectedRoot);
        const existingIds = (matchedSuite?.testcases || []).map(tc => tc.id);
        const maxIdNum = Math.max(
          0,
          ...existingIds.map(id => {
            const match = id.match(/TC(\d+)/i);
            return match ? parseInt(match[1]) : 0;
          })
        );

        const newId = `TC${maxIdNum + 1}`;
        const saveIdInput = document.getElementById('saveId');
        if (saveIdInput) saveIdInput.value = newId;
      });
    });
});
