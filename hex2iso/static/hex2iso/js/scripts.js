require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.33.0/min/vs' }});
require(['vs/editor/editor.main'], function () {
  const jsonEditor = monaco.editor.create(document.getElementById('json-editor'), {
    language: 'json',
    theme: 'vs-dark',
    automaticLayout: true,
    wordWrap: 'on',
    value: ''
  });

  const hexEditor = monaco.editor.create(document.getElementById('hex-editor'), {
    language: 'plaintext',
    theme: 'vs-dark',
    automaticLayout: true,
    wordWrap: 'on',
    value: ''
  });

  let currentSchema = '';
  let isUpdating = false;

  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  async function convert(input, direction) {
    if (!currentSchema || !input.trim()) return '';
    const response = await fetch('/hex2iso/convert/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ input, direction, schema: currentSchema })
    });
    return await response.text();
  }

  async function fetchSchemas() {
    const res = await fetch('/hex2iso/list_schemas/');
    const schemas = await res.json();

    const schemaButtonsContainer = document.getElementById('schema-buttons');

    schemas.forEach(name => {
      const btn = document.createElement('button');
      btn.className = 'schema-btn';
      btn.textContent = name.replace('_schema.json', '');
      btn.dataset.schema = name;

      btn.onclick = async () => {
        currentSchema = name;
        document.querySelectorAll('.schema-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const jsonVal = jsonEditor.getValue().trim();
        const hexVal = hexEditor.getValue().trim();

        if (jsonVal && !jsonVal.includes("Enter JSON data")) {
          const result = await convert(jsonVal, 'json_to_hex');
          hexEditor.setValue(result);
        } else if (hexVal) {
          const result = await convert(hexVal, 'hex_to_json');
          jsonEditor.setValue(result);
        }
      };

      schemaButtonsContainer.appendChild(btn);
    });
  }

  function setupSmartJsonPlaceholder(editor, placeholderJson) {
    let placeholderActive = true;
  
    editor.setValue(placeholderJson);
    editor.getModel().updateOptions({ tabSize: 2 });
  
    editor.onDidFocusEditorText(() => {
      if (placeholderActive) {
        placeholderActive = false;
        editor.setValue(''); // Clears JSON immediately on click
      }
    });
  
    editor.onDidBlurEditorText(() => {
      const value = editor.getValue().trim();
      if (!value) {
        placeholderActive = true;
        editor.setValue(placeholderJson); // Resets placeholder if empty
      }
    });
  }
  

  function setupSmartHexPlaceholder(editor, placeholderText) {
    let placeholderActive = true;
  
    editor.setValue(placeholderText);
    editor.getModel().updateOptions({ tabSize: 2 });
  
    editor.onDidFocusEditorText(() => {
      if (placeholderActive) {
        placeholderActive = false;
        editor.setValue(''); // Clear on click
      }
    });
  
    editor.onDidBlurEditorText(() => {
      const value = editor.getValue().trim();
      if (!value) {
        placeholderActive = true;
        editor.setValue(placeholderText); // Restore if empty
      }
    });
  }
  
  // Setup placeholder only for JSON editor
  setupSmartJsonPlaceholder(
    jsonEditor,
    JSON.stringify({ message: "Enter JSON data..." }, null, 2)
  );
  setupSmartHexPlaceholder(
    hexEditor,
    'Place hex dump here...'
  );
  
  // Real-time conversion
  jsonEditor.onDidChangeModelContent(async () => {
    if (!currentSchema || isUpdating) return;

    const jsonVal = jsonEditor.getValue().trim();
    if (jsonVal === '' || jsonVal.includes("Enter JSON data")) return;

    isUpdating = true;
    const result = await convert(jsonVal, 'json_to_hex');
    hexEditor.setValue(result);
    isUpdating = false;
  });

  hexEditor.onDidChangeModelContent(async () => {
    if (!currentSchema || isUpdating) return;

    const hexVal = hexEditor.getValue().trim();
    if (hexVal === '') return;

    isUpdating = true;
    const result = await convert(hexVal, 'hex_to_json');
    jsonEditor.setValue(result);
    isUpdating = false;
  });

  function handleCopy(content, btnId) {
    navigator.clipboard.writeText(content).then(() => {
      const btn = document.getElementById(btnId);
      const original = btn.textContent;
      btn.textContent = '✅';
      setTimeout(() => btn.textContent = original, 1000);
    });
  }

  document.getElementById('copy-json').onclick = () => handleCopy(jsonEditor.getValue(), 'copy-json');
  document.getElementById('copy-hex').onclick = () => handleCopy(hexEditor.getValue(), 'copy-hex');

  fetchSchemas();
});
