const filenames = JSON.parse(document.getElementById('json-files').textContent);
const treeContainer = document.getElementById('testcaseTree');
const selectedTestCases = new Set();
let loadedTestcase = null;

// Build collapsible tree for each JSON file
filenames.forEach(filename => {
  const folder = document.createElement('div');
  folder.className = 'tree-item tree-folder';
  folder.innerHTML = `<span class="folder-icon">▶</span><span class="folder-label">${filename}</span>`;

  const subContainer = document.createElement('div');
  subContainer.className = 'tree-indent';
  const subtree = document.createElement('div');
  subtree.className = 'tree-subtree collapsed';
  subContainer.appendChild(subtree);

  treeContainer.appendChild(folder);
  treeContainer.appendChild(subContainer);

  let loaded = false;

  folder.addEventListener('click', () => {
    const icon = folder.querySelector('.folder-icon');
    const isCollapsed = subtree.classList.toggle('collapsed');
    icon.textContent = isCollapsed ? '▶' : '▼';

    if (!loaded && !isCollapsed) {
      fetch(`/load_testcase/${filename}/`)
        .then(res => res.ok ? res.json() : Promise.reject(`Failed to load ${filename}`))
        .then(data => {
          buildTree(data, subtree);
          loaded = true;
        })
        .catch(err => {
          subtree.innerHTML = `<div style="color: red;">Error loading ${filename}.json</div>`;
          console.error(err);
        });
    }
  });
});

function buildTree(data, container) {
  data.forEach(item => {
    const file = document.createElement('div');
    file.className = 'tree-item tree-file';
    file.textContent = `${item.id} - ${item.name || item.description || 'Unnamed Test'}`;
    file.dataset.testcase = JSON.stringify(item);

    file.addEventListener('click', (e) => {
      e.stopPropagation();
      const parsed = JSON.parse(file.dataset.testcase);
      loadedTestcase = parsed;
      document.getElementById('deleteSelectedBtn').disabled = false;

      if (e.ctrlKey || e.metaKey) {
        const selected = file.classList.toggle('selected');
        selected ? selectedTestCases.add(file.dataset.testcase) : selectedTestCases.delete(file.dataset.testcase);
        document.getElementById('deleteSelectedBtn').disabled = selectedTestCases.size === 0;
      } else {
        document.querySelectorAll('.tree-file.selected').forEach(el => el.classList.remove('selected'));
        file.classList.add('selected');
        monacoEditor?.setValue(JSON.stringify(parsed.request, null, 2));
        document.getElementById('currentTestName').textContent = parsed.name || parsed.id;
        document.getElementById('selectedTestBadge').classList.remove('hidden');
      }
    });

    container.appendChild(file);
  });
}

// Collapse all button
document.getElementById('collapseAllBtn').addEventListener('click', () => {
  document.querySelectorAll('.tree-subtree').forEach(subtree => subtree.classList.add('collapsed'));
  document.querySelectorAll('.tree-folder .folder-icon').forEach(icon => icon.textContent = '▶');
});

document.getElementById('deleteSelectedBtn').disabled = true;
