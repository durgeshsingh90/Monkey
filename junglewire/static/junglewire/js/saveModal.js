document.getElementById('saveBtn').addEventListener('click', () => {
  document.getElementById('saveModal').classList.remove('hidden');
  document.getElementById('modalTitle').textContent = loadedTestcase ? "Update Test Case" : "Add New Test Case";

  // Assume you’ve created a global object to map files to roots:
  // e.g. { "certifications": ["Visa Authorization Suite"], "demo": ["Root 1", "Root 2"] }
  populateDropdownsFromFiles(testcaseFileRootMap);

  if (loadedTestcase) {
    document.getElementById('saveId').value = loadedTestcase.id || '';
    document.getElementById('saveName').value = loadedTestcase.name || '';
  } else {
    document.getElementById('saveName').value = '';
    document.getElementById('saveId').value = '';
  }
});

document.getElementById('saveBtn').addEventListener('click', () => {
  document.getElementById('saveModal').classList.remove('hidden');
  document.getElementById('modalTitle').textContent = loadedTestcase ? "Update Test Case" : "Add New Test Case";

  // Clear existing dropdowns
  const fileSelect = document.getElementById('fileSelect');
  const rootSelect = document.getElementById('rootSelect');
  fileSelect.innerHTML = '<option value="">Loading...</option>';
  rootSelect.innerHTML = '<option value="">Select a file first</option>';

  // Step 1: Load list of files
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

  // Step 2: When file selected, load roots
  fileSelect.addEventListener('change', () => {
    const selectedFile = fileSelect.value;
    rootSelect.innerHTML = '<option value="">Loading roots...</option>';
    if (!selectedFile) return;

    fetch(`/junglewire/load_testcase/${selectedFile}`)
      .then(res => res.ok ? res.json() : Promise.reject("Failed to load file"))
      .then(data => {
        const roots = Array.isArray(data) ? data.map(s => s.name) : [data.name];
        rootSelect.innerHTML = '<option value="">Select Root Suite</option>';
        roots.forEach(r => {
          const opt = document.createElement('option');
          opt.value = r;
          opt.textContent = r;
          rootSelect.appendChild(opt);
        });
      });
  });

  // Pre-fill inputs if editing
  if (loadedTestcase) {
    document.getElementById('saveId').value = loadedTestcase.id || '';
    document.getElementById('saveName').value = loadedTestcase.name || '';
  } else {
    document.getElementById('saveId').value = '';
    document.getElementById('saveName').value = '';
  }
});

document.getElementById('cancelSaveBtn').addEventListener('click', () => {
  document.getElementById('saveModal').classList.add('hidden');
});

fileSelect.addEventListener('change', () => {
  const selectedFile = fileSelect.value;
  rootSelect.innerHTML = '<option value="">Loading roots...</option>';
  if (!selectedFile) return;

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

      // Auto-generate TC ID when user selects root
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
        document.getElementById('saveId').value = newId;
      });
    });
});
