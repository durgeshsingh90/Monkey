require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.33.0/min/vs' } });

let inputEditor, outputEditor;
let currentTheme = localStorage.getItem('monacoTheme') || 'vs-dark'; // Get theme from localStorage or use dark as default

require(['vs/editor/editor.main'], function () {
  initEditors();
});

function initEditors() {
  // Input Editor
  inputEditor = monaco.editor.create(document.getElementById('input-editor'), {
    value: '',
    language: 'json',
    theme: currentTheme,
    automaticLayout: true,
    minimap: { enabled: false }
  });

  // Output Editor (Read-only)
  try {
    outputEditor = monaco.editor.create(document.getElementById('output-editor'), {
      value: '',
      language: 'json',
      theme: currentTheme,
      readOnly: true,
      automaticLayout: true,
      minimap: { enabled: false }
    });
  } catch (error) {
    console.error('Error initializing output editor:', error);
  }

  updateThemeButtonIcon();

  // Real-time validation while typing
  inputEditor.onDidChangeModelContent(() => {
    const rawInput = inputEditor.getValue();
    updateJsonStatus(rawInput);
  });

  // Handle paste events (instant validation after paste)
  inputEditor.getDomNode().addEventListener('paste', () => {
    setTimeout(() => {
      const rawInput = inputEditor.getValue();
      updateJsonStatus(rawInput);
    }, 10);
  });
}

function toggleTheme() {
  currentTheme = currentTheme === 'vs-light' ? 'vs-dark' : 'vs-light';
  monaco.editor.setTheme(currentTheme);
  localStorage.setItem('monacoTheme', currentTheme); // Save preference
  updateThemeButtonIcon();
}

function updateThemeButtonIcon() {
  const btn = document.getElementById('toggleThemeBtn');
  if (currentTheme === 'vs-dark') {
    btn.innerText = '🌙 Dark';
  } else {
    btn.innerText = '🌞 Light';
  }
}

function updateJsonStatus(text) {
  const model = inputEditor.getModel();
  const statusElement = document.getElementById('json-status');

  if (text.trim() === '') {
    statusElement.style.display = 'none';
    monaco.editor.setModelMarkers(model, 'json', []);
    return;
  }

  statusElement.style.display = 'inline-block';

  try {
    JSON.parse(text);
    monaco.editor.setModelMarkers(model, 'json', []);
    statusElement.innerText = "Status: ✅ Valid JSON";
    statusElement.style.color = "limegreen";
  } catch (error) {
    monaco.editor.setModelMarkers(model, 'json', [{
      startLineNumber: 1,
      startColumn: 1,
      endLineNumber: 1,
      endColumn: 1,
      message: "Invalid JSON: " + error.message,
      severity: monaco.MarkerSeverity.Error
    }]);
    statusElement.innerText = "Status: ❌ Invalid JSON";
    statusElement.style.color = "red";
  }
}

function cleanData() {
  const rawText = inputEditor.getValue();
  const cleanedJsonBlocks = extractJsonBlocks(rawText);

  if (cleanedJsonBlocks.length === 0) {
    alert("❌ No JSON blocks found.");
    inputEditor.setValue("");
    updateJsonStatus("");
    return;
  }

  const jsonObjects = cleanedJsonBlocks.map(jsonStr => {
    try {
      return JSON.parse(jsonStr);
    } catch (e) {
      console.warn("Skipped invalid JSON block during parsing:", jsonStr);
      return null;
    }
  }).filter(obj => obj !== null);

  const requests100 = [];
  const responses110 = [];

  jsonObjects.forEach(obj => {
    const mti = obj.mti;
    const de037 = obj?.data_elements?.DE037 || obj?.data_elements?.DE037?.trim();

    if (!de037) {
      console.warn("Skipped message without DE037:", obj);
      return;
    }

    if (mti === 100 || mti === "100") {
      requests100.push({ rrn: de037, message: obj });
    } else if (mti === 110 || mti === "110") {
      responses110.push({ rrn: de037, message: obj });
    }
  });

  const groupedMessages = [];

  requests100.forEach((request) => {
    const rrn = request.rrn;
    const matchingResponse = responses110.find(response => response.rrn === rrn);

    const group = [];

    // Push request
    group.push(request.message);

    // Push response if exists
    if (matchingResponse) {
      group.push(matchingResponse.message);
    }

    groupedMessages.push(group);
  });

  const finalJsonString = JSON.stringify(groupedMessages, null, 4);

  inputEditor.setValue(finalJsonString);
  updateJsonStatus(finalJsonString);
}

function copyOutput() {
  const copyBtn = document.getElementById('copyBtn');

  if (!outputEditor) {
    console.error('outputEditor is not initialized.');
    return;
  }

  const outputText = outputEditor.getValue();

  if (!navigator.clipboard) {
    fallbackCopyTextToClipboard(outputText);
    return;
  }

  navigator.clipboard.writeText(outputText)
    .then(() => {
      copyBtn.innerText = "Copied!";
      copyBtn.style.color = "green";
      copyBtn.classList.add("copied");

      setTimeout(() => {
        copyBtn.innerText = "Copy Output";
        copyBtn.style.color = "";
        copyBtn.classList.remove("copied");
      }, 1000);
    })
    .catch(err => {
      console.error('❌ Failed to copy:', err);
      fallbackCopyTextToClipboard(outputText);  // Use fallback method if clipboard API fails
    });
}

function fallbackCopyTextToClipboard(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();

  try {
    const successful = document.execCommand('copy');
    if (successful) {
      const copyBtn = document.getElementById('copyBtn');
      copyBtn.innerText = "Copied!";
      copyBtn.style.color = "green";
      copyBtn.classList.add("copied");

      setTimeout(() => {
        copyBtn.innerText = "Copy Output";
        copyBtn.style.color = "";
        copyBtn.classList.remove("copied");
      }, 1000);
    } else {
      console.error('Failed to copy to clipboard using fallback method.');
    }
  } catch (err) {
    console.error('Fallback: Oops, unable to copy', err);
  }

  document.body.removeChild(textArea);
}


async function handleAction(actionName) {
  console.log(`${actionName} button clicked!`);

  const inputJson = inputEditor.getValue();

  let parsedData;
  try {
    parsedData = JSON.parse(inputJson);
  } catch (error) {
    alert("❌ Invalid JSON in the input box!");
    return;
  }

  try {
    const response = await fetch(`/gen_reversals/generate-reversal/${encodeURIComponent(actionName)}/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()  // Add CSRF token to headers if necessary
      },
      body: JSON.stringify(parsedData)
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error("Server responded with error:", errorData);
      alert(`❌ Error from server: ${errorData.error || response.status}`);
      return;
    }

    const reversalMessages = await response.json();
    const formattedJson = JSON.stringify(reversalMessages, null, 4);
    outputEditor.setValue(formattedJson);

  } catch (error) {
    console.error("❌ Failed to send data to the server:", error);
    alert("❌ Failed to send data to the server.");
  }
}

function extractJsonBlocks(text) {
  const blocks = [];
  let braceCount = 0;
  let startIndex = -1;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    if (char === '{') {
      if (braceCount === 0) {
        startIndex = i;
      }
      braceCount++;
    } else if (char === '}') {
      braceCount--;
      if (braceCount === 0 && startIndex !== -1) {
        const jsonBlock = text.slice(startIndex, i + 1);
        try {
          JSON.parse(jsonBlock);
          blocks.push(jsonBlock);
        } catch (e) {
          console.warn("Skipped invalid JSON block:", jsonBlock);
        }
        startIndex = -1;
      }
    }
  }

  return blocks;
}

function getCSRFToken() {
  const cookieValue = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)')?.pop() || '';
  return cookieValue;
}
