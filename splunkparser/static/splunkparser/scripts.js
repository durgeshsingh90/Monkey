
// ✅ CSRF Helper Function
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const csrftoken = getCookie('csrftoken');
let editor;
let defaultContent = `Paste your Splunk logs here...`;

document.addEventListener("DOMContentLoaded", () => {
  initMonacoEditor();
  setupOutputSelectionListener();
  clearOutputFile();
  document.getElementById('copyButton').addEventListener('click', copyOutput);
  document.getElementById('defaultButton').addEventListener('click', setDefault);
});

async function clearOutputFile() {
  try {
    const response = await fetch('/splunkparser/clear_output/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken }
    });
    if (!response.ok) console.error('Failed to clear output.json');
  } catch (error) {
    console.error('Error clearing output.json:', error);
  }
}

function initMonacoEditor() {
  require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.34.1/min/vs' } });
  require(['vs/editor/editor.main'], () => {
    editor = monaco.editor.create(document.getElementById('editor'), {
      value: defaultContent,
      language: 'plaintext',
      theme: 'vs-dark',
      automaticLayout: true
    });
    const savedLogs = localStorage.getItem('splunkLogs');
    if (savedLogs) editor.setValue(savedLogs);
    editor.onDidChangeModelContent(() => localStorage.setItem('splunkLogs', editor.getValue()));
    editor.onDidChangeCursorSelection(updateEditorSelection);
  });
}

function updateEditorSelection() {
  if (!editor) return;
  const selection = editor.getSelection();
  const selectedText = editor.getModel().getValueInRange(selection);
  document.getElementById('editorSelectionCount').innerText = selectedText.length;
}

function setupOutputSelectionListener() {
  const outputContent = document.getElementById('outputArea');
  const outputSelectionCount = document.getElementById('outputSelectionCount');
  outputContent.addEventListener('mouseup', updateOutputSelection);
  outputContent.addEventListener('keyup', updateOutputSelection);
  function updateOutputSelection() {
    const selectedText = window.getSelection().toString();
    outputSelectionCount.innerText = selectedText.length;
  }
}

async function parseLogsToJSON() {
  const logData = editor.getValue().trim();
  if (!logData) return notify("Please provide log data to parse.");
  try {
    const data = await sendLogsToBackend(logData);
    if (data.status === 'error' || !data.result) return notify(`❌ Error: ${data.message}`);
    const jsonOutput = JSON.stringify(data.result, null, 2);
    displayOutput(jsonOutput, 'language-json');
  } catch (error) {
    notify(`❌ Error: ${error.message}`);
  }
}

async function sendLogsToBackend(logData) {
  const response = await fetch('/splunkparser/parse/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
    body: JSON.stringify({ log_data: logData })
  });
  if (!response.ok) throw new Error(`Server Error: ${response.status}`);
  return await response.json();
}

function displayOutput(content, languageClass) {
  const output = document.getElementById('outputArea');
  output.textContent = content;
  output.className = languageClass;
  Prism.highlightElement(output);
  notify("");
  saveOutputFile(content);
}

async function saveOutputFile(content) {
  try {
    const response = await fetch('/splunkparser/save_output/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify({ output_data: content })
    });
    if (!response.ok) notify(`❌ Failed to save output.json`);
  } catch (error) {
    notify(`❌ Error saving output.json: ${error.message}`);
  }
}

function copyOutput() {
  const output = document.getElementById('outputArea').textContent;
  const copyButton = document.getElementById('copyButton');
  navigator.clipboard.writeText(output).then(() => {
    copyButton.textContent = 'Copied!';
    setTimeout(() => { copyButton.textContent = 'Copy Output'; }, 1000);
  }).catch(err => notify(`❌ Failed to copy: ${err.message}`));
}

async function setDefault() {
  try {
    const response = await fetch('/splunkparser/set_default/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      }
    });

    const data = await response.json();

    if (data.status === 'success') {
      const jsonOutput = JSON.stringify(data.result, null, 2);
      displayOutput(jsonOutput, 'language-json');

      // ✅ Show scheme & card name in notification
      notify(`✅ Default values applied.\nScheme: ${data.scheme}\n | Card: ${data.cardName}`);

      const defaultBtn = document.getElementById('defaultButton');
      defaultBtn.textContent = 'Added!';
      defaultBtn.classList.add('added');

      setTimeout(() => {
        defaultBtn.textContent = 'Set Default';
        defaultBtn.classList.remove('added');
      }, 1000);
    } else {
      notify(`❌ ${data.message}`);
    }
  } catch (error) {
    notify(`❌ Error: ${error.message}`);
  }
}


function openConfig() {
  window.location.href = '/splunkparser/settings/';
}

function notify(message) {
  const notification = document.getElementById('notification');
  if (notification) notification.textContent = message;
}
