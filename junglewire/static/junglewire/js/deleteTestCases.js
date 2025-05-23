document.getElementById('deleteSelectedBtn').addEventListener('click', () => {
  if (selectedTestCases.size === 0) {
    alert("No test cases selected.");
    return;
  }

  const grouped = {};

  for (const tc of selectedTestCases) {
    try {
      const parsed = JSON.parse(tc);
      const file = parsed.__source;
      const root = parsed.__root;
      if (!grouped[file]) grouped[file] = {};
      if (!grouped[file][root]) grouped[file][root] = [];
      grouped[file][root].push(parsed.id);
    } catch {}
  }

  if (!confirm(`Are you sure you want to delete ${selectedTestCases.size} test case(s)?`)) {
    return;
  }

  fetch('/junglewire/delete_testcases/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({ to_delete: grouped })
  })
    .then(res => res.ok ? res.json() : Promise.reject("Delete failed"))
    .then(data => {
      alert("✅ Deleted successfully.");
      // Save open folders and selected test cases
const openFolders = Array.from(document.querySelectorAll('.tree-subtree:not(.collapsed)'))
  .map(el => el.dataset.key);
const selectedIds = Array.from(selectedTestCases);

localStorage.setItem('junglewire_openFolders', JSON.stringify(openFolders));
localStorage.setItem('junglewire_selectedCases', JSON.stringify(selectedIds));

      location.reload();  // Easy: reload the page to show updates
    })
    .catch(err => {
      console.error(err);
      alert("❌ Failed to delete test cases.");
    });
});
