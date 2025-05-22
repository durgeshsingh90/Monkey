document.getElementById('deleteSelectedBtn').addEventListener('click', () => {
  const idsToDelete = new Set();

  if (selectedTestCases.size > 0) {
    for (const tc of selectedTestCases) {
      try {
        const parsed = JSON.parse(tc);
        if (parsed?.id) idsToDelete.add(parsed.id);
      } catch {}
    }
  } else if (loadedTestcase?.id) {
    idsToDelete.add(loadedTestcase.id);
  }

  if (idsToDelete.size === 0) {
    alert("No test cases selected to delete.");
    return;
  }

  if (!confirm(`Are you sure you want to delete ${idsToDelete.size} test case(s)?`)) return;

  let deletedCount = 0;

  const recurseDelete = (obj) => {
    if (Array.isArray(obj)) {
      for (let i = obj.length - 1; i >= 0; i--) {
        if (idsToDelete.has(obj[i].id)) {
          obj.splice(i, 1);
          deletedCount++;
        }
      }
    } else if (typeof obj === 'object' && obj !== null) {
      for (const key in obj) recurseDelete(obj[key]);
    }
  };

  recurseDelete(testcaseData);

  if (deletedCount > 0) {
    alert(`Deleted ${deletedCount} test case(s).`);
  } else {
    alert("Test case(s) not found.");
    return;
  }

  selectedTestCases.clear();
  loadedTestcase = null;

  document.getElementById('deleteSelectedBtn').disabled = true;
  document.getElementById('selectedTestBadge').classList.add('hidden');
  monacoEditor.setValue('');
  document.getElementById('testcaseTree').innerHTML = '';
  buildTree(testcaseData, document.getElementById('testcaseTree'));

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
    console.log('✅ Saved testcases.json');
  })
  .catch(err => {
    console.error('❌ Save failed:', err);
    alert('Failed to save changes to testcases.json. Please try again.');
  });
});
