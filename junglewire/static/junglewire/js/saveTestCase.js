// Button visual feedback (success/error)
function showSaveFeedback(status) {
  const saveBtn = document.getElementById('saveBtn');
  if (status === 'saved') {
    saveBtn.textContent = "Saved";
    saveBtn.classList.add('saved');
    setTimeout(() => {
      saveBtn.textContent = "Save";
      saveBtn.classList.remove('saved');
    }, 1000);
  } else if (status === 'error') {
    saveBtn.textContent = "Error";
    saveBtn.classList.add('error');
    setTimeout(() => {
      saveBtn.textContent = "Save";
      saveBtn.classList.remove('error');
    }, 1500);
  }
}

// Save test case (create or update)
function saveTestCase() {
  const file = document.getElementById('fileSelect')?.value.trim();
  const root = document.getElementById('rootSelect')?.value.trim();
  const nameInput = document.getElementById('saveName')?.value.trim();
  const saveBtn = document.getElementById('saveConfirmBtn');

  if (!file || !root) {
    alert("Please select both file and root.");
    return;
  }

  // Get current test case JSON from editor
  let updatedRequest;
  try {
    updatedRequest = monacoEditor ? JSON.parse(monacoEditor.getValue()) : {};
  } catch (e) {
    alert('Invalid JSON in the editor');
    return;
  }

  // Load existing JSON data for selected file from localStorage
  const storedData = localStorage.getItem(`testcases-${file}`);
  if (!storedData) {
    alert('File content not loaded.');
    return;
  }

  let parsedData;
  try {
    parsedData = JSON.parse(storedData);
  } catch (err) {
    alert('Error parsing stored JSON');
    return;
  }

  // Normalize data to an array of root-level suites
  const suites = Array.isArray(parsedData) ? parsedData : [parsedData];

  const targetSuite = suites.find(s => s.name === root);
  if (!targetSuite || !Array.isArray(targetSuite.testcases)) {
    alert(`Root "${root}" not found in file.`);
    return;
  }

  // Generate new test case ID based on max existing ID
  const existingIds = targetSuite.testcases.map(tc => tc.id);
  const maxIdNum = Math.max(
    0,
    ...existingIds.map(id => {
      const match = id.match(/^TC(\d+)/i);
      return match ? parseInt(match[1]) : 0;
    })
  );
  const newId = `TC${maxIdNum + 1}`;

  const fullName = nameInput ? `${newId} - ${nameInput}` : newId;

  const newEntry = {
    id: newId,
    name: fullName,
    request: updatedRequest
  };

  targetSuite.testcases.push(newEntry);

  // Show visual feedback
  saveBtn.textContent = 'Saving...';
  saveBtn.disabled = true;

  fetch(`/junglewire/save_testcases/${file}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify(suites.length === 1 ? suites[0] : suites)
  })
    .then(res => {
      if (!res.ok) throw new Error('Save failed');
      return res.json();
    })
    .then(() => {
      alert('Test case saved!');
      document.getElementById('saveModal').classList.add('hidden');
      loadedTestcase = newEntry;
      document.getElementById('currentTestName').textContent = fullName;
      document.getElementById('selectedTestBadge').classList.remove('hidden');
    })
    .catch(err => {
      console.error('Save error:', err);
      alert('Failed to save test case. See console for details.');
    })
    .finally(() => {
      saveBtn.textContent = 'Save';
      saveBtn.disabled = false;
    });
}

// JSON validation for Save button state
function validateEditorJSON() {
  const saveBtn = document.getElementById('saveBtn');
  try {
    JSON.parse(monacoEditor.getValue());
    saveBtn.classList.remove('disabled');
    saveBtn.disabled = false;
    saveBtn.title = "Save Test Case";
  } catch {
    saveBtn.classList.add('disabled');
    saveBtn.disabled = true;
    saveBtn.title = "Invalid JSON – cannot save";
  }
}

document.getElementById('saveBtn').addEventListener('click', () => {
  saveTestCase(); // Call without `isSaveAs`
});


function saveTestCase() {
  const id = document.getElementById('saveId').value.trim();
  const nameInput = document.getElementById('saveName').value.trim();
  const file = document.getElementById('fileSelect').value.trim();
  const root = document.getElementById('rootSelect').value.trim();
  const saveBtn = document.getElementById('saveBtn');

  if (!id || !file || !root) {
    alert("Please select a file and root. ID must be auto-generated.");
    return;
  }

  const name = nameInput ? `${id} - ${nameInput}` : id;

  let updatedRequest;
  try {
    updatedRequest = monacoEditor ? JSON.parse(monacoEditor.getValue()) : {};
  } catch (e) {
    alert('Invalid JSON in editor');
    return;
  }

  const newEntry = { id, name, request: updatedRequest };

  // Load from localStorage for editing
  const storedData = localStorage.getItem(`testcases-${file}`);
  let parsedData = [];

  if (storedData) {
    try {
      parsedData = JSON.parse(storedData);
    } catch (err) {
      alert('Error parsing stored JSON');
      return;
    }
  }

  let targetSuite = parsedData.find(suite => suite.name === root);
  if (!targetSuite) {
    alert(`Root '${root}' not found`);
    return;
  }

  const existingIndex = targetSuite.testcases.findIndex(tc => tc.id === id);
  if (existingIndex !== -1) {
    targetSuite.testcases[existingIndex] = newEntry;
  } else {
    targetSuite.testcases.push(newEntry);
  }

  saveBtn.textContent = 'Saving...';
  saveBtn.disabled = true;

  fetch(`/junglewire/save_testcases/${file}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify(parsedData)
  })
    .then(res => res.ok ? res.json() : Promise.reject('Save failed'))
    .then(() => {
      alert('Saved successfully!');
      document.getElementById('saveModal').classList.add('hidden');
      loadedTestcase = newEntry;
      document.getElementById('currentTestName').textContent = newEntry.name;
      document.getElementById('selectedTestBadge').classList.remove('hidden');
    })
    .catch(err => {
      console.error(err);
      alert('Error saving. Check console.');
    })
    .finally(() => {
      saveBtn.textContent = 'Save';
      saveBtn.disabled = false;
    });
}
