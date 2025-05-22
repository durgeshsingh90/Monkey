let selectedFolderPath = [];  // Example: ["certified", "Fiserv", "Authorization Tests"]
const deleteGif = "/static/junglewire/images/delete.gif";
const deletePng = "/static/junglewire/images/delete.png";


const exclusiveButtons = ['dev77', 'paypal77', 'novate', 'test77', 'cert77', 'netscaler'];
exclusiveButtons.forEach(id => {
  document.getElementById(id).addEventListener('click', function () {
    exclusiveButtons.forEach(btnId => {
      document.getElementById(btnId).classList.remove('active');
    });
    this.classList.add('active');
  });
});

// Independent toggles
['updateBtn', 'echoBtn', 'incrBtn'].forEach(id => {
  document.getElementById(id).addEventListener('click', function () {
    this.classList.toggle('active');
  });
});

// Line number logic for Container 2 textarea
const hexInput = document.getElementById('hexInput');
const lineNumbers = document.getElementById('lineNumbers');
const lineNumbersWrapper = document.getElementById('lineNumbersWrapper');

function updateLineNumbers() {
  const lineCount = hexInput.value.split('\n').length;
  lineNumbers.textContent = Array.from({ length: lineCount }, (_, i) => i + 1).join('\n');
}
hexInput.addEventListener('input', updateLineNumbers);
hexInput.addEventListener('scroll', () => {
  lineNumbersWrapper.scrollTop = hexInput.scrollTop;
});
updateLineNumbers();

// Copy & Clear
const copyBtn = document.getElementById('copyBtn');
const clearBtn = document.getElementById('clearBtn');
const logViewer = document.getElementById('logViewer');

copyBtn.addEventListener('click', () => {
  navigator.clipboard.writeText(logViewer.value).then(() => {
    const original = copyBtn.textContent;
    copyBtn.textContent = "Copied";
    setTimeout(() => copyBtn.textContent = original, 1000);
  });
});

clearBtn.addEventListener('click', () => {
  logViewer.value = '';
  const original = clearBtn.textContent;
  clearBtn.textContent = "Cleared";
  setTimeout(() => clearBtn.textContent = original, 1000);
});

// Monaco and Test Case Explorer
const testcaseData = JSON.parse(document.getElementById('testcase-data').textContent);
const treeContainer = document.getElementById('testcaseTree');
let monacoEditor;
let loadedTestcase = null;
const selectedTestCases = new Set();

require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' } });
require(['vs/editor/editor.main'], function () {
  if (!monacoEditor) {
    monacoEditor = monaco.editor.create(document.getElementById('editor'), {
      value: '',
      language: 'json',
      theme: 'vs-dark',
      automaticLayout: true
    });

    // ✅ Attach listener after editor is initialized
    monacoEditor.onDidChangeModelContent(() => {
      validateEditorJSON();
    });
  }

  buildTree(testcaseData, treeContainer);
});

function validateEditorJSON() {
  const saveBtn = document.getElementById('saveBtn');
  try {
    const value = monacoEditor.getValue();
    JSON.parse(value);
    saveBtn.classList.remove('disabled');
    saveBtn.title = "Save Test Case";
  } catch (e) {
    saveBtn.classList.add('disabled');
    saveBtn.title = "Invalid JSON – cannot save";
  }
}


function buildTree(data, container, path = []) {
  if (Array.isArray(data)) {
    data.forEach(item => {
      const file = document.createElement('div');
      file.className = 'tree-item tree-file';
      file.textContent = `${item.id} - ${item.name || item.description || 'Unnamed Test'}`;
      file.dataset.testcase = JSON.stringify(item);
      

      file.addEventListener('click', (e) => {
        e.stopPropagation();
        const key = file.dataset.testcase;
        const parsed = JSON.parse(key);
        loadedTestcase = parsed;
        document.getElementById('deleteSelectedBtn').disabled = false;


if (e.ctrlKey || e.metaKey) {
  const selected = file.classList.toggle('selected');
  selected ? selectedTestCases.add(key) : selectedTestCases.delete(key);
  document.getElementById('deleteSelectedBtn').disabled = selectedTestCases.size === 0;

} else {
  // Clear all previous selections
  document.querySelectorAll('.tree-file.selected').forEach(el => el.classList.remove('selected'));

  // Highlight the one clicked
  file.classList.add('selected');

  // Load into editor
  if (monacoEditor) {
    monacoEditor.setValue(JSON.stringify(parsed.request, null, 2));
  }

  // Set current test name badge
  document.getElementById('currentTestName').textContent = parsed.name || parsed.id || 'Unnamed Test';
  document.getElementById('selectedTestBadge').classList.remove('hidden');
}


        console.log("Selected:", [...selectedTestCases].map(JSON.parse));
      });

      container.appendChild(file);
    });
  } else if (typeof data === 'object' && data !== null) {
Object.entries(data).forEach(([key, value]) => {
  const folder = document.createElement('div');
  folder.className = 'tree-item tree-folder';
  folder.innerHTML = `<span class="folder-icon">▶</span><span class="folder-label">${key}</span>`;

  const subContainer = document.createElement('div');
  subContainer.className = 'tree-indent';

  const subtree = document.createElement('div');
  subtree.className = 'tree-subtree';
  subContainer.appendChild(subtree);
  container.appendChild(folder);
  container.appendChild(subContainer);

  folder.addEventListener('click', (e) => {
    e.stopPropagation();
    const icon = folder.querySelector('.folder-icon');
    const subtree = folder.nextElementSibling?.querySelector('.tree-subtree');
    if (subtree) {
      const isCollapsed = subtree.classList.toggle('collapsed');
      icon.textContent = isCollapsed ? '▶' : '▼';
      if (!e.ctrlKey && !e.metaKey) {
        selectedFolderPath = path.concat(key);
        console.log("Folder Path:", selectedFolderPath);
      }

      if (e.ctrlKey || e.metaKey) {
        subtree.classList.remove('collapsed');
        icon.textContent = '▼';
        const files = subtree.querySelectorAll('.tree-file');
        files.forEach(file => {
          const key = file.dataset.testcase;
          if (!selectedTestCases.has(key)) {
            selectedTestCases.add(key);
            file.classList.add('selected');
          }
        });
      }
    }
  });

  buildTree(value, subtree, path.concat(key));
});


  }
}

// Scheduled API Call
document.getElementById('scheduledBtn').addEventListener('click', () => {
  fetch('/api/schedule/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({
      action: 'schedule_now',
      testcases: [...selectedTestCases].map(JSON.parse)
    })
  })
    .then(res => res.ok ? res.json() : Promise.reject('Failed'))
    .then(data => alert('Scheduled: ' + data.message))
    .catch(err => {
      console.error(err);
      alert('Scheduling failed.');
    });
});

function getCSRFToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}

// Save Modal Logic
document.getElementById('saveBtn').addEventListener('click', () => {
  document.getElementById('saveModal').classList.remove('hidden');
  document.getElementById('modalTitle').textContent = loadedTestcase ? "Update Test Case" : "Add New Test Case";

  populateDropdowns(testcaseData);

  if (loadedTestcase) {
    document.getElementById('saveId').value = loadedTestcase.id || '';
    document.getElementById('saveName').value = loadedTestcase.name || '';
  } else {
    // default name blank
    document.getElementById('saveName').value = '';
    document.getElementById('saveId').value = ''; // we'll populate it after folder selection
  }
});
document.getElementById('saveConfirmBtn').addEventListener('click', () => {
  saveTestCase(false); // regular save (update)
});

document.getElementById('saveAsBtn').addEventListener('click', () => {
  saveTestCase(true); // save as new
});


document.getElementById('cancelSaveBtn').addEventListener('click', () => {
  document.getElementById('saveModal').classList.add('hidden');
});
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
    // Update existing
    targetArray[existingIndex] = newEntry;
  } else {
    if (existingIndex !== -1) {
      showSaveError(feedbackImg);
      alert(`Test case ID "${id}" already exists.`);
      return;
    }
    targetArray.push(newEntry);
  }

  // Show saving animation
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

      buildTree(testcaseData, treeContainer);
    })
    .catch(err => {
      console.error('Save error:', err);
      showSaveError(feedbackImg);
      alert('Error saving file.');
    });
}



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

  const confirmDelete = confirm(`Are you sure you want to delete ${idsToDelete.size} test case(s)?`);
  if (!confirmDelete) return;

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
  buildTree(testcaseData, treeContainer);

  console.log("Sending data to backend:", testcaseData); // ✅ Log before saving

  fetch('/api/save_testcases/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify(testcaseData)
  })
  .then(res => {
    if (!res.ok) throw new Error('Save failed');
    return res.json();
  })
  .then(() => {
    console.log('✅ Saved testcases.json');
  })
  .catch(err => {
    console.error('❌ Save failed:', err);
    alert('Failed to save changes to testcases.json. Please try again.');
  });
});


function populateDropdowns(data) {
  const l1 = document.getElementById('level1Select');
  const l2 = document.getElementById('level2Select');
  const l3 = document.getElementById('level3Select');

  l1.innerHTML = '<option value="">Select Level 1</option>';
  Object.keys(data).forEach(k => {
    if (typeof data[k] === 'object') {
      l1.innerHTML += `<option value="${k}">${k}</option>`;
    }
  });

  l1.onchange = () => {
    l2.innerHTML = '<option value="">Select Level 2</option>';
    l3.innerHTML = '<option value="">Select Level 3</option>';
    const level2Obj = data[l1.value] || {};
    Object.keys(level2Obj).forEach(k => {
      if (typeof level2Obj[k] === 'object') {
        l2.innerHTML += `<option value="${k}">${k}</option>`;
      }
    });
  };

  l2.onchange = () => {
    l3.innerHTML = '<option value="">Select Level 3</option>';
    const level3Obj = (data[l1.value] || {})[l2.value] || {};
    Object.keys(level3Obj).forEach(k => {
      if (Array.isArray(level3Obj[k])) {
        l3.innerHTML += `<option value="${k}">${k}</option>`;
      }
    });
  };
  l3.onchange = () => {
  const level3Obj = (data[l1.value] || {})[l2.value] || {};
  l3.innerHTML = '<option value="">Select Level 3</option>';

  Object.keys(level3Obj).forEach(k => {
    if (Array.isArray(level3Obj[k])) {
      l3.innerHTML += `<option value="${k}">${k}</option>`;
    }
  });

  // After population, wait for user to choose l3
l3.addEventListener('change', () => {
  if (!loadedTestcase && l1.value && l2.value && l3.value) {
    const tcArray = data[l1.value][l2.value][l3.value];
    const existingIds = tcArray.map(t => t.id || '');

    // Extract numeric parts from IDs like TC1.1, TC2, etc.
    let maxBase = 0;
    existingIds.forEach(id => {
      const match = id.match(/^TC(\d+)/i);
      if (match) {
        const num = parseInt(match[1]);
        if (!isNaN(num) && num > maxBase) maxBase = num;
      }
    });

    const newId = `TC${maxBase + 1}`;
    document.getElementById('saveId').value = newId;
  }
}, { once: true });


}

function showSaveSuccess(imgEl) {
  imgEl.src = "/static/junglewire/images/saving.gif";
  setTimeout(() => {
    imgEl.src = "/static/junglewire/images/save.png";
  }, 1500);
}

function showSaveError(imgEl) {
  imgEl.src = "/static/junglewire/images/error.gif";
  setTimeout(() => {
    imgEl.src = "/static/junglewire/images/save.png";
  }, 1500);
}
}
document.getElementById('collapseAllBtn').addEventListener('click', () => {
  // Collapse all subtrees
  const allSubtrees = document.querySelectorAll('.tree-subtree');
  allSubtrees.forEach(subtree => subtree.classList.add('collapsed'));

  // Update folder icons to closed ▶
  const allIcons = document.querySelectorAll('.tree-folder .folder-icon');
  allIcons.forEach(icon => icon.textContent = '▶');
});


document.getElementById('deleteSelectedBtn').disabled = true;
