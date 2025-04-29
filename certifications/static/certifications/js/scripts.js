let editor;
let hot;
let currentJsonData = {};

// Initialize Monaco
require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.38.0/min/vs' }});
require(["vs/editor/editor.main"], function () {
  editor = monaco.editor.create(document.getElementById('json-editor'), {
    value: '',
    language: 'json',
    theme: 'vs-dark',
    automaticLayout: true
  });
});

// Fetch and render tree
fetch('/certifications/get_structure/')
  .then(res => res.json())
  .then(data => renderTree(data));

function renderTree(data) {
  const container = document.getElementById('tree-container');
  container.innerHTML = '';

  for (const group in data) {
    const groupEl = createCollapsible(group);

    for (const user in data[group]) {
      const userEl = createCollapsible(user);

      for (const testcase in data[group][user]) {
        const tcEl = document.createElement('li');
        tcEl.innerHTML = `<span class="testcase">🧪 ${testcase}</span>`;
        tcEl.querySelector('.testcase').addEventListener('click', () => {
          fetch(`/certifications/get_testcase_data/?group=${encodeURIComponent(group)}&user=${encodeURIComponent(user)}&testcase=${encodeURIComponent(testcase)}`)
            .then(res => res.json())
            .then(tcData => {
              currentJsonData = tcData;
              editor.setValue(JSON.stringify(tcData, null, 2));
              loadGrid(tcData);
              showJsonView(); // Always switch to JSON view when a test case is clicked
            });
        });
        userEl.querySelector('.nested').appendChild(tcEl);
      }

      groupEl.querySelector('.nested').appendChild(userEl);
    }

    container.appendChild(groupEl);
  }
}

function createCollapsible(name) {
  const wrapper = document.createElement('li');
  wrapper.classList.add('collapsible');
  wrapper.innerHTML = `<span>➕ ${name}</span><ul class="nested"></ul>`;

  wrapper.querySelector('span').addEventListener('click', function() {
    this.parentElement.querySelector('.nested').classList.toggle('active');
    this.textContent = this.textContent.startsWith('➕') ? '➖ ' + name : '➕ ' + name;
  });

  return wrapper;
}

// Handle toggle view
document.getElementById('toggle-view').addEventListener('click', function() {
  const grid = document.getElementById('grid-view');
  const jsonEditor = document.getElementById('json-editor');

  if (grid.style.display === 'none') {
    saveGridToJson();
    grid.style.display = 'block';
    jsonEditor.style.display = 'none';
    this.innerText = 'Switch to JSON View';
    loadGrid(currentJsonData);
  } else {
    grid.style.display = 'none';
    jsonEditor.style.display = 'block';
    this.innerText = 'Switch to Grid View';
    saveGridToJson();
  }
});

function loadGrid(jsonData) {
  const container = document.getElementById('grid-view');
  if (hot) hot.destroy();

  const rows = [];

  if (jsonData.mti !== undefined) {
    rows.push({ Field: 'MTI', Value: jsonData.mti });
  }

  const de = jsonData.data_elements || {};
  for (const [key, value] of Object.entries(de)) {
    if (typeof value === 'object' && value !== null) {
      for (const [nestedKey, nestedValue] of Object.entries(value)) {
        rows.push({ Field: `${key}.${nestedKey}`, Value: nestedValue });
      }
    } else {
      rows.push({ Field: key, Value: value });
    }
  }

  hot = new Handsontable(container, {
    data: rows,
    colHeaders: ['Field', 'Value'],
    columns: [{ data: 'Field' }, { data: 'Value' }],
    stretchH: 'all',
    autoWrapRow: true,
    rowHeaders: true,
    height: '80vh',
    licenseKey: 'non-commercial-and-evaluation'
  });
}

function saveGridToJson() {
  const gridData = hot ? hot.getData() : [];
  const newJson = { mti: null, data_elements: {} };

  gridData.forEach(([field, value]) => {
    if (!field) return;
    if (field === 'MTI') {
      newJson.mti = value;
    } else if (field.includes('.')) {
      const [mainKey, subKey] = field.split('.');
      if (!newJson.data_elements[mainKey]) {
        newJson.data_elements[mainKey] = {};
      }
      newJson.data_elements[mainKey][subKey] = value;
    } else {
      newJson.data_elements[field] = value;
    }
  });

  currentJsonData = newJson;
  editor.setValue(JSON.stringify(currentJsonData, null, 2));
}

function showJsonView() {
  document.getElementById('grid-view').style.display = 'none';
  document.getElementById('json-editor').style.display = 'block';
  document.getElementById('toggle-view').innerText = 'Switch to Grid View';
}

