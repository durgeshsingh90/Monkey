
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
  if (typeof require === 'undefined') {
    const loaderScript = document.createElement('script');
    loaderScript.src = 'https://cdn.jsdelivr.net/npm/monaco-editor@0.34.1/min/vs/loader.js';
    loaderScript.onload = () => {
      configureAndLoadMonaco();
    };
    document.head.appendChild(loaderScript);
  } else {
    configureAndLoadMonaco();
  }

  function configureAndLoadMonaco() {
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

      editor.onDidChangeModelContent(() => {
        localStorage.setItem('splunkLogs', editor.getValue());
      });

      editor.onDidChangeCursorSelection(updateEditorSelection);
    });
  }
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
    const response = await fetch('/splunkparser/parse/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({ log_data: logData })
    });

    const data = await response.json();
    if (data.status !== 'success') {
      return notify(`❌ Error: ${data.message}`);
    }

    const fullMessages = data.messages;

    // Show only result section in output
const resultOnly = fullMessages.map(msg => msg.result);


    document.getElementById('outputArea').textContent = JSON.stringify(resultOnly, null, 2);
    document.getElementById('validationArea').textContent = JSON.stringify(fullMessages, null, 2);

    Prism.highlightElement(document.getElementById('outputArea'));
    Prism.highlightElement(document.getElementById('validationArea'));

    notify(`✅ Parsed ${fullMessages.length} messages`);

  } catch (error) {
    notify(`❌ Error: ${error.message}`);
  }
}


async function saveOutputFileAndValidate(content) {
  try {
    const saveResponse = await fetch('/splunkparser/save_output/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
      body: JSON.stringify({ output_data: content })
    });

    if (!saveResponse.ok) {
      notify(`❌ Failed to save output.json`);
      return;
    }

    // ✅ Trigger validation
    const validateResponse = await fetch('/splunkparser/validate_output/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken }
    });

    if (!validateResponse.ok) {
      notify(`❌ Validation failed.`);
      return;
    }

    const validationResult = await validateResponse.json();

    if (validationResult.status === 'success') {
      const wrongLength = validationResult.validation.wrong_length.length;
      const wrongFormat = validationResult.validation.wrong_format.length;
      const totalIssues = wrongLength + wrongFormat;

      if (totalIssues > 0) {
        notify(`⚠️ Validation completed with ${totalIssues} issues (Wrong Length: ${wrongLength}, Wrong Format: ${wrongFormat})`);
        console.log(validationResult.validation);
      } else {
        notify(`✅ All fields and subfields passed validation!`);
      }
    } else {
      notify(`❌ Validation request failed.`);
    }

  } catch (error) {
    notify(`❌ Error during save/validate: ${error.message}`);
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
    if (!response.ok) {
      notify(`❌ Failed to save output.json`);
      return;
    }

    // ✅ After saving, call validate_output
    await validateOutputAndShowMessage();

  } catch (error) {
    notify(`❌ Error saving output.json: ${error.message}`);
  }
}
async function validateOutputAndShowMessage() {
  try {
    const response = await fetch('/splunkparser/validate_output/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken }
    });
    if (!response.ok) {
      notify(`❌ Validation failed`);
      return;
    }

    const data = await response.json();
    if (data.status === 'success') {
      notify(data.message);

      // ✅ Now display full validation details
      const validationArea = document.getElementById('validationArea');
      validationArea.textContent = JSON.stringify(data.validation, null, 2);
      Prism.highlightElement(validationArea);
      
    } else {
      notify(`⚠️ Validation warning: ${data.message}`);
    }
  } catch (error) {
    notify(`❌ Error validating output: ${error.message}`);
  }
}



function copyOutput() {
  const output = document.getElementById('outputArea').textContent;
  const copyButton = document.getElementById('copyButton');

  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(output).then(() => {
      copyButton.textContent = 'Copied!';
      setTimeout(() => { copyButton.textContent = 'Copy Output'; }, 1000);
    }).catch(err => notify(`❌ Clipboard error: ${err.message}`));
  } else {
    const textarea = document.createElement('textarea');
    textarea.value = output;
    textarea.style.position = 'fixed';
    textarea.style.opacity = 0;
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    try {
      const successful = document.execCommand('copy');
      if (successful) {
        copyButton.textContent = 'Copied!';
        setTimeout(() => { copyButton.textContent = 'Copy Output'; }, 1000);
      } else {
        notify('❌ Fallback copy failed');
      }
    } catch (err) {
      notify(`❌ Fallback error: ${err.message}`);
    }
    document.body.removeChild(textarea);
  }
}



async function setDefault() {
  const logData = editor.getValue().trim();
  const presentDEs = Array.from(logData.matchAll(/(?:in|out)\[\s*(\d+):?\s*\]</g))
                          .map(match => match[1].padStart(3, '0'))
                          .map(de => `DE${de}`);

  try {
    const response = await fetch('/splunkparser/set_default/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({ present_fields: presentDEs })  // ✅ pass only DEs found in text
    });

    const data = await response.json();

    if (data.status === 'success') {
      const jsonOutput = JSON.stringify(data.result, null, 2);
      displayOutput(jsonOutput, 'language-json');
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
