// Exclusive group logic
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
  }
  buildTree(testcaseData, treeContainer);
});

function buildTree(data, container) {
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

        if (e.ctrlKey || e.metaKey) {
          const selected = file.classList.toggle('selected');
          selected ? selectedTestCases.add(key) : selectedTestCases.delete(key);
        } else {
          if (monacoEditor) {
            monacoEditor.setValue(JSON.stringify(parsed.request, null, 2));
          }
        }

        console.log("Selected:", [...selectedTestCases].map(JSON.parse));
      });

      container.appendChild(file);
    });
  } else if (typeof data === 'object') {
    Object.entries(data).forEach(([key, value]) => {
      const folder = document.createElement('div');
      folder.className = 'tree-item tree-folder';
      folder.innerHTML = `<span class="folder-icon">▶</span> <span class="folder-label">${key}</span>`;
      container.appendChild(folder);

      const subContainer = document.createElement('div');
      subContainer.className = 'tree-indent';

      const subtree = document.createElement('div');
      subtree.className = 'tree-subtree';

      subContainer.appendChild(subtree);
      container.appendChild(subContainer);

      buildTree(value, subtree);

      folder.addEventListener('click', (e) => {
        e.stopPropagation();
        const icon = folder.querySelector('.folder-icon');

        if (e.ctrlKey || e.metaKey) {
          const files = subContainer.querySelectorAll('.tree-file');
          const anyUnselected = [...files].some(f => !f.classList.contains('selected'));
          files.forEach(file => {
            const key = file.dataset.testcase;
            if (anyUnselected) {
              file.classList.add('selected');
              selectedTestCases.add(key);
            } else {
              file.classList.remove('selected');
              selectedTestCases.delete(key);
            }
          });
          console.log("Selected:", [...selectedTestCases].map(JSON.parse));
        } else {
          const isCollapsed = subContainer.classList.toggle('collapsed');
          icon.textContent = isCollapsed ? '▶' : '▼';
        }
      });
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


document.getElementById('cancelSaveBtn').addEventListener('click', () => {
  document.getElementById('saveModal').classList.add('hidden');
});
document.getElementById('saveConfirmBtn').addEventListener('click', () => {
  const id = document.getElementById('saveId').value.trim();
  const name = document.getElementById('saveName').value.trim();
  const l1 = document.getElementById('level1Select').value;
  const l2 = document.getElementById('level2Select').value;
  const l3 = document.getElementById('level3Select').value;
  const feedbackImg = document.getElementById('saveFeedbackImg');

  if (!id || !name || !l1 || !l2 || !l3) {
    feedbackImg.src = '/static/junglewire/images/error.gif';
    setTimeout(() => feedbackImg.src = '/static/junglewire/images/save.png', 1500);
    alert('All fields required');
    return;
  }

  const updatedRequest = monacoEditor ? JSON.parse(monacoEditor.getValue()) : {};
  const newEntry = { id, name, request: updatedRequest };

  const targetArray = testcaseData?.[l1]?.[l2]?.[l3];

  if (!Array.isArray(targetArray)) {
    feedbackImg.src = '/static/junglewire/images/error.gif';
    setTimeout(() => feedbackImg.src = '/static/junglewire/images/save.png', 1500);
    alert('Invalid folder selection');
    return;
  }

  const existingIndex = targetArray.findIndex(t => t.id === id);
  if (!loadedTestcase || (loadedTestcase && loadedTestcase.id !== id)) {
    if (existingIndex !== -1) {
      feedbackImg.src = '/static/junglewire/images/error.gif';
      setTimeout(() => feedbackImg.src = '/static/junglewire/images/save.png', 1500);
      alert(`Test case ID "${id}" already exists.`);
      return;
    }
  }

  if (existingIndex !== -1) {
    targetArray[existingIndex] = newEntry;
  } else {
    targetArray.push(newEntry);
  }

  // Show saving animation
  feedbackImg.src = '/static/junglewire/images/saving.gif';

  // Send updated JSON to server
  fetch('/api/save_testcases/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify(testcaseData)
  })
    .then(res => res.ok ? res.json() : Promise.reject('Save failed'))
    .then(data => {
      feedbackImg.src = '/static/junglewire/images/save.png';
      alert('Saved successfully!');
      document.getElementById('saveModal').classList.add('hidden');
    })
    .catch(err => {
      console.error('Save error:', err);
      feedbackImg.src = '/static/junglewire/images/error.gif';
      setTimeout(() => feedbackImg.src = '/static/junglewire/images/save.png', 1500);
      alert('Error saving file.');
    });
});


document.getElementById('deleteBtn').addEventListener('click', () => {
  if (!loadedTestcase) return alert('Nothing to delete');
  let deleted = false;

  const recurseDelete = (obj) => {
    if (Array.isArray(obj)) {
      const idx = obj.findIndex(t => t.id === loadedTestcase.id);
      if (idx !== -1) {
        obj.splice(idx, 1);
        deleted = true;
        return;
      }
    } else if (typeof obj === 'object') {
      for (let key in obj) recurseDelete(obj[key]);
    }
  };

  recurseDelete(testcaseData);
  if (deleted) {
    alert('Test case deleted.');
    loadedTestcase = null;
    document.getElementById('saveModal').classList.add('hidden');
  } else {
    alert('Test case not found.');
  }
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