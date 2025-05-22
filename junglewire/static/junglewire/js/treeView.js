const filenames = JSON.parse(document.getElementById('json-files').textContent);
const treeContainer = document.getElementById('testcaseTree');
document.getElementById('deleteSelectedBtn').disabled = true;

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
  // Toggle all test cases under this file (across all roots)
  const files = rootContainer.querySelectorAll('.tree-file');
  const anyUnselected = Array.from(files).some(file => !file.classList.contains('selected'));

  files.forEach(file => {
    const key = file.dataset.testcase;
    const shouldSelect = anyUnselected;
    file.classList.toggle('selected', shouldSelect);
    shouldSelect ? selectedTestCases.add(key) : selectedTestCases.delete(key);
  });

  document.getElementById('deleteSelectedBtn').disabled = selectedTestCases.size === 0;
  return; // ✅ Skip expand/collapse
}


    const icon = fileBar.querySelector('.folder-icon');
    const isCollapsed = rootContainer.classList.toggle('collapsed');
    icon.textContent = isCollapsed ? '▶' : '▼';

    if (!loaded && !isCollapsed) {
      fetch(`/junglewire/load_testcase/${filename}`)
        .then(res => res.ok ? res.json() : Promise.reject("Failed to load"))
        .then(fileData => {
          const rootLabel = `${fileData.name || 'Unnamed Suite'}${fileData.description ? ' — ' + fileData.description : ''}`;
          const rootBar = document.createElement('div');
          rootBar.className = 'tree-item tree-folder tree-bar root-bar';
          rootBar.innerHTML = `<span class="folder-icon">▶</span><span class="folder-label">${rootLabel}</span>`;

          const rootIndent = document.createElement('div');
          rootIndent.className = 'tree-indent';
          const testcasesContainer = document.createElement('div');
          testcasesContainer.className = 'tree-subtree collapsed';
          rootIndent.appendChild(testcasesContainer);

          rootContainer.appendChild(rootBar);
          rootContainer.appendChild(rootIndent);

          if (Array.isArray(fileData.testcases)) {
            fileData.testcases.forEach(item => {
              const label = `${item.id}${item.name ? ' - ' + item.name : ''}${item.description ? ' — ' + item.description : ''}`;
              const testItem = document.createElement('div');
              testItem.className = 'tree-item tree-file';
              testItem.textContent = label;
              testItem.dataset.testcase = JSON.stringify(item);

              testItem.addEventListener('click', (e) => {
                e.stopPropagation();
                const parsed = JSON.parse(testItem.dataset.testcase);
                loadedTestcase = parsed;
                document.getElementById('deleteSelectedBtn').disabled = false;

                if (e.ctrlKey || e.metaKey) {
                  const selected = testItem.classList.toggle('selected');
                  selected ? selectedTestCases.add(testItem.dataset.testcase) : selectedTestCases.delete(testItem.dataset.testcase);
                  document.getElementById('deleteSelectedBtn').disabled = selectedTestCases.size === 0;
                } else {
                  document.querySelectorAll('.tree-file.selected').forEach(el => el.classList.remove('selected'));
                  testItem.classList.add('selected');
                  monacoEditor?.setValue(JSON.stringify(parsed.request, null, 2));
                  document.getElementById('currentTestName').textContent = parsed.name || parsed.id;
                  document.getElementById('selectedTestBadge').classList.remove('hidden');
                }
              });

              testcasesContainer.appendChild(testItem);
            });
          }

          rootBar.addEventListener('click', (e) => {
            e.stopPropagation();

            if (e.ctrlKey || e.metaKey) {
              // Ctrl+Click: toggle all test cases under this root
              testcasesContainer.querySelectorAll('.tree-file').forEach(file => {
                const key = file.dataset.testcase;
                const selected = file.classList.toggle('selected');
                selected ? selectedTestCases.add(key) : selectedTestCases.delete(key);
              });
              document.getElementById('deleteSelectedBtn').disabled = selectedTestCases.size === 0;
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
            }
          });

          // Auto-expand root
          testcasesContainer.classList.remove('collapsed');
          rootBar.querySelector('.folder-icon').textContent = '▼';

          loaded = true;
        })
        .catch(err => {
          rootContainer.innerHTML = `<div style="color:red;">Error loading test cases</div>`;
          console.error(err);
        });
    } else if (!isCollapsed) {
      rootContainer.querySelectorAll('.tree-file').forEach(file => {
        const key = file.dataset.testcase;
        if (!selectedTestCases.has(key)) {
          file.classList.add('selected');
          selectedTestCases.add(key);
        }
      });
      document.getElementById('deleteSelectedBtn').disabled = false;
    }
  });
});

document.getElementById('collapseAllBtn').addEventListener('click', () => {
  document.querySelectorAll('.tree-subtree').forEach(subtree => subtree.classList.add('collapsed'));
  document.querySelectorAll('.tree-folder .folder-icon').forEach(icon => icon.textContent = '▶');
});
