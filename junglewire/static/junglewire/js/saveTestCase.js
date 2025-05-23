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

function saveTestCase() {
  const id = document.getElementById('saveId').textContent.trim(); // was input, now div
  const nameInputEl = document.getElementById('saveName');
  const fileEl = document.getElementById('fileSelect');
  const rootEl = document.getElementById('rootSelect');
  const dbSelect = document.getElementById('databaseSelect');
  const saveBtn = document.getElementById('saveConfirmBtn');

  if (!id || !fileEl.value.trim() || !rootEl.value.trim()) {
    alert("Please select a file and root. ID must be auto-generated.");
    return;
  }

  const name = nameInputEl.value.trim();
  const file = fileEl.value.trim();
  const root = rootEl.value.trim();
  const selectedDatabases = Array.from(dbSelect.selectedOptions).map(opt => opt.value);

  let updatedRequest;
  try {
    updatedRequest = monacoEditor ? JSON.parse(monacoEditor.getValue()) : {};
  } catch (e) {
    alert('Invalid JSON in editor');
    return;
  }

  const newEntry = {
    id,
    name,
    request: updatedRequest,
    databases: selectedDatabases
  };

  saveBtn.textContent = 'Saving...';
  saveBtn.disabled = true;

  fetch(`/junglewire/save_testcases/${file}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({
      root: root,
      testcase: newEntry
    })
  })
    .then(res => res.ok ? res.json() : Promise.reject('Save failed'))
    .then(() => {
      alert('Saved successfully!');
      document.getElementById('saveModal')?.classList.add('hidden');
      loadedTestcase = newEntry;
      const currentTestNameEl = document.getElementById('currentTestName');
      const badgeEl = document.getElementById('selectedTestBadge');
      if (currentTestNameEl) currentTestNameEl.textContent = newEntry.name;
      if (badgeEl) badgeEl.classList.remove('hidden');
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



// Bind save function
document.getElementById('saveConfirmBtn')?.addEventListener('click', () => {
  saveTestCase();
});

