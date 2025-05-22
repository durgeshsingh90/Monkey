function saveTestCase(isSaveAs = false) {
  const id = document.getElementById('saveId').value.trim();
  const name = document.getElementById('saveName').value.trim();
  const [l1, l2, l3] = selectedFolderPath;
  const feedbackImg = document.getElementById('saveFeedbackImg');

  if (!id || !name || !l1 || !l2 || !l3) {
    showSaveError(feedbackImg);
    alert('All fields required and a folder must be selected.');
    return;
  }

  let updatedRequest;
  try {
    updatedRequest = monacoEditor ? JSON.parse(monacoEditor.getValue()) : {};
  } catch (e) {
    showSaveError(feedbackImg);
    alert('Invalid JSON');
    return;
  }

  const newEntry = { id, name, request: updatedRequest };
  const targetArray = testcaseData?.[l1]?.[l2]?.[l3];

  if (!Array.isArray(targetArray)) {
    showSaveError(feedbackImg);
    alert('Invalid folder selection');
    return;
  }

  const existingIndex = targetArray.findIndex(t => t.id === id);

  if (!isSaveAs && loadedTestcase?.id === id) {
    targetArray[existingIndex] = newEntry;
  } else {
    if (existingIndex !== -1) {
      showSaveError(feedbackImg);
      alert(`Test case ID "${id}" already exists.`);
      return;
    }
    targetArray.push(newEntry);
  }

  feedbackImg.src = '/static/junglewire/images/saving.gif';

  fetch('/api/save_testcases/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify(testcaseData)
  })
    .then(res => res.ok ? res.json() : Promise.reject('Save failed'))
    .then(() => {
      feedbackImg.src = '/static/junglewire/images/save.png';
      alert('Saved successfully!');
      document.getElementById('saveModal').classList.add('hidden');

      loadedTestcase = isSaveAs ? null : newEntry;
      document.getElementById('currentTestName').textContent = newEntry.name || newEntry.id || 'Unnamed Test';
      document.getElementById('selectedTestBadge').classList.add('hidden');
      buildTree(testcaseData, document.getElementById('testcaseTree'));
    })
    .catch(err => {
      console.error('Save error:', err);
      showSaveError(feedbackImg);
      alert('Error saving file.');
    });
}

function showSaveError(imgEl) {
  imgEl.src = "/static/junglewire/images/error.gif";
  setTimeout(() => {
    imgEl.src = "/static/junglewire/images/save.png";
  }, 1500);
}
