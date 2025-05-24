const filenames = JSON.parse(document.getElementById('json-files').textContent);
const treeContainer = document.getElementById('testcaseTree');
document.getElementById('deleteSelectedBtn').disabled = true;

function updateLogViewerFromSelection() {
  const grouped = {};
  for (const tc of selectedTestCases) {
    try {
      const parsed = JSON.parse(tc);
      const filename = parsed.__source || 'unknown.json';
      if (!grouped[filename]) grouped[filename] = [];
      grouped[filename].push(parsed.id);
    } catch {}
  }
  const lines = Object.entries(grouped).map(([file, ids]) => `${file} → ${ids.join(', ')}`);
  document.getElementById('logViewer').value = lines.join('\n');
}

filenames.forEach(filename => {
  const fileBar = document.createElement('div');
  fileBar.className = 'tree-item tree-folder tree-bar file-bar';
  fileBar.innerHTML = `<span class="folder-icon">▶</span><span class="folder-label">${filename}</span>`;

  const fileIndent = document.createElement('div');
  fileIndent.className = 'tree-indent';
  const rootContainer = document.createElement('div');
  rootContainer.className = 'tree-subtree collapsed';
  fileIndent.appendChild(rootContainer);

  treeContainer.appendChild(fileBar);
  treeContainer.appendChild(fileIndent);

  let loaded = false;

  fileBar.addEventListener('click', (e) => {
    if ((e.ctrlKey || e.metaKey) && loaded) {
      const files = rootContainer.querySelectorAll('.tree-file');
      const anyUnselected = Array.from(files).some(f => !f.classList.contains('selected'));
      files.forEach(file => {
        const key = file.dataset.testcase;
        file.classList.toggle('selected', anyUnselected);
        anyUnselected ? selectedTestCases.add(key) : selectedTestCases.delete(key);
      });
      document.getElementById('deleteSelectedBtn').disabled = selectedTestCases.size === 0;
      updateLogViewerFromSelection();
      return;
    }

    const icon = fileBar.querySelector('.folder-icon');
    const isCollapsed = rootContainer.classList.toggle('collapsed');
    icon.textContent = isCollapsed ? '▶' : '▼';

    const openFiles = new Set(JSON.parse(localStorage.getItem('openFiles') || '[]'));
    if (!isCollapsed) openFiles.add(filename); else openFiles.delete(filename);
    localStorage.setItem('openFiles', JSON.stringify([...openFiles]));

    if (!loaded && !isCollapsed) {
      fetch(`/junglewire/load_testcase/${filename}`)
        .then(res => res.ok ? res.json() : Promise.reject("Failed to load"))
        .then(fileData => {
          const fileSuites = Array.isArray(fileData) ? fileData : [fileData];

          fileSuites.forEach(suite => {
            const rootLabel = `${suite.name || 'Unnamed Suite'}${suite.description ? ' — ' + suite.description : ''}`;
            const rootBar = document.createElement('div');
            rootBar.className = 'tree-item tree-folder tree-bar root-bar';
            rootBar.innerHTML = `<span class="folder-icon">▶</span><span class="folder-label">${rootLabel}</span>`;

            const rootIndent = document.createElement('div');
            rootIndent.className = 'tree-indent';
            const testcasesContainer = document.createElement('div');
            testcasesContainer.className = 'tree-subtree collapsed';
            testcasesContainer.dataset.key = `${filename}::${suite.name}`;
            rootIndent.appendChild(testcasesContainer);

            rootBar.addEventListener('click', (e) => {
              e.stopPropagation();

              if (e.ctrlKey || e.metaKey) {
                const files = testcasesContainer.querySelectorAll('.tree-file');
                const anyUnselected = Array.from(files).some(f => !f.classList.contains('selected'));
                files.forEach(file => {
                  const key = file.dataset.testcase;
                  file.classList.toggle('selected', anyUnselected);
                  anyUnselected ? selectedTestCases.add(key) : selectedTestCases.delete(key);
                });
                document.getElementById('deleteSelectedBtn').disabled = selectedTestCases.size === 0;
                updateLogViewerFromSelection();
                return;
              }

              const icon = rootBar.querySelector('.folder-icon');
              const isCollapsed = testcasesContainer.classList.toggle('collapsed');
              icon.textContent = isCollapsed ? '▶' : '▼';

              if (!isCollapsed) {
                testcasesContainer.querySelectorAll('.tree-file').forEach(file => {
                  const key = file.dataset.testcase;
                  if (!selectedTestCases.has(key)) {
                    file.classList.add('selected');
                    selectedTestCases.add(key);
                  }
                });
                document.getElementById('deleteSelectedBtn').disabled = false;
                updateLogViewerFromSelection();
              }
            });

            if (Array.isArray(suite.testcases)) {
              suite.testcases.forEach(item => {
                const label = `${item.id}${item.name ? ' - ' + item.name : ''}${item.description ? ' — ' + item.description : ''}`;
                const testItem = document.createElement('div');
                testItem.className = 'tree-item tree-file';
                testItem.textContent = label;
                const enrichedItem = Object.assign({}, item, {
                  __source: filename,
                  __root: suite.name || 'Unnamed Suite'
                });
                testItem.dataset.testcase = JSON.stringify(enrichedItem);

                testItem.addEventListener('click', (e) => {
                  e.stopPropagation();
                  const parsed = JSON.parse(testItem.dataset.testcase);
                  loadedTestcase = parsed;

                  if (e.ctrlKey || e.metaKey) {
                    const selected = testItem.classList.toggle('selected');
                    selected ? selectedTestCases.add(testItem.dataset.testcase) : selectedTestCases.delete(testItem.dataset.testcase);
                    document.getElementById('deleteSelectedBtn').disabled = selectedTestCases.size === 0;
                    updateLogViewerFromSelection();
                  } else {
                    document.querySelectorAll('.tree-file.selected').forEach(el => el.classList.remove('selected'));
                    testItem.classList.add('selected');
                    selectedTestCases.clear();
                    selectedTestCases.add(testItem.dataset.testcase);
                    updateLogViewerFromSelection();
const formattedJSON = {
  mti: parsed.mti || "0200",  // fallback for safety
  data_elements: parsed.request || {}
};

monacoEditor?.setValue(JSON.stringify(formattedJSON, null, 2));

// Also convert JSON → hex and show in #hexInput
fetch('/convert/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCSRFToken()
  },
  body: JSON.stringify({
    direction: 'json_to_hex',
    schema: 'omnipay.json',  // change if needed
    input: JSON.stringify(formattedJSON)
  })
})
.then(res => res.ok ? res.json() : Promise.reject('Conversion failed'))
.then(data => {
  document.getElementById('hexInput').value = data.hex || '';
  updateLineNumbers();
})
.catch(err => {
  console.error('Failed to convert JSON to hex:', err);
});
                    document.getElementById('currentTestName').textContent = parsed.name || parsed.id;
                    document.getElementById('selectedTestBadge').classList.remove('hidden');
                  }
                });

                testcasesContainer.appendChild(testItem);
              });
            }

            rootContainer.appendChild(rootBar);
            rootContainer.appendChild(rootIndent);

            const openKeys = JSON.parse(localStorage.getItem('openFiles') || '[]');
            if (openKeys.includes(filename)) {
              testcasesContainer.classList.remove('collapsed');
              rootBar.querySelector('.folder-icon').textContent = '▼';
            }
          });

          loaded = true;
        })
        .catch(err => {
          rootContainer.innerHTML = `<div style="color:red;">Error loading test cases</div>`;
          console.error(err);
        });
    }
  });
});

document.getElementById('collapseAllBtn').addEventListener('click', () => {
  document.querySelectorAll('.tree-subtree').forEach(subtree => subtree.classList.add('collapsed'));
  document.querySelectorAll('.tree-folder .folder-icon').forEach(icon => icon.textContent = '▶');
  localStorage.removeItem('openFiles');
});

document.getElementById('selectAllBtn').addEventListener('click', () => {
  const treeFiles = document.querySelectorAll('.tree-file');
  if (treeFiles.length === 0) {
    const allFileBars = document.querySelectorAll('.file-bar');
    allFileBars.forEach(bar => bar.click());
    setTimeout(() => document.getElementById('selectAllBtn').click(), 300);
    return;
  }

  selectedTestCases.clear();
  treeFiles.forEach(file => {
    file.classList.add('selected');
    selectedTestCases.add(file.dataset.testcase);
  });

  document.getElementById('deleteSelectedBtn').disabled = false;
  updateLogViewerFromSelection();
});

function getCSRFToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}
