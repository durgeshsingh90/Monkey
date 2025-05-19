// Exclusive group logic
const exclusiveButtons = [
  'dev77', 'paypal77', 'novate', 'test77', 'cert77', 'netscaler'
];
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
      file.textContent = `${item.id} - ${item.name}`;
      file.onclick = () => {
        if (monacoEditor) {
          monacoEditor.setValue(JSON.stringify(item.request, null, 2));
        }
      };
      container.appendChild(file);
    });
  } else if (typeof data === 'object') {
    Object.entries(data).forEach(([key, value]) => {
      const folder = document.createElement('div');
      folder.className = 'tree-item tree-folder';
      folder.textContent = key;
      container.appendChild(folder);

      const subContainer = document.createElement('div');
      subContainer.className = 'tree-item';
      container.appendChild(subContainer);

      buildTree(value, subContainer);
    });
  }
}

// Optional: Send button
const sendBtn = document.getElementById('sendBtn');
if (sendBtn) {
  sendBtn.addEventListener('click', () => {
    alert('Send button clicked!');
  });
}
