document.getElementById('saveBtn').addEventListener('click', () => {
  document.getElementById('saveModal').classList.remove('hidden');
  document.getElementById('modalTitle').textContent = loadedTestcase ? "Update Test Case" : "Add New Test Case";
  populateDropdowns(testcaseData);

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
