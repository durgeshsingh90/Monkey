require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.33.0/min/vs' } });
require(['vs/editor/editor.main'], function () {
  let userHasEdited = false;
  let currentSchema = '';
  let isUpdating = false;

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

  function setModelValueSafely(editor, value) {
    isUpdating = true;
    editor.setValue(value);
    isUpdating = false;
  }

  const savedJson = localStorage.getItem('jsonEditorContent');
  const savedHex = localStorage.getItem('hexEditorContent');
  if (savedJson) setModelValueSafely(jsonEditor, savedJson);
  if (savedHex) setModelValueSafely(hexEditor, savedHex);

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
      btn.textContent = name.replace('.json', '');
      btn.dataset.schema = name;

      btn.onclick = async () => {
        currentSchema = name;
        localStorage.setItem('selectedSchema', name);
        document.querySelectorAll('.schema-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      
        const jsonVal = jsonEditor.getValue().trim();
        const hexVal = hexEditor.getValue().trim();
      
        if (!userHasEdited || (!jsonVal && !hexVal)) return;
      
        try {
          if (jsonVal.startsWith('{')) {
            const result = await convert(jsonVal, 'json_to_hex');
            setModelValueSafely(hexEditor, result);
          } else if (/^[0-9A-Fa-f\s]+$/.test(hexVal)) {
            const result = await convert(hexVal, 'hex_to_json');
            setModelValueSafely(jsonEditor, JSON.stringify(JSON.parse(result), null, 2));
          }
        } catch (err) {
          console.warn("Conversion failed:", err);
        }
      };

      schemaButtonsContainer.appendChild(btn);
    });

    // just visually restore active button, don't click or convert
    const savedSchema = localStorage.getItem('selectedSchema');
    if (savedSchema) {
      const savedButton = [...document.querySelectorAll('.schema-btn')]
        .find(btn => btn.dataset.schema === savedSchema);
      if (savedButton) {
        savedButton.classList.add('active');
        currentSchema = savedSchema;
      }
    }
  }

  jsonEditor.onDidChangeModelContent(async () => {
    if (!currentSchema || isUpdating) return;
    userHasEdited = true;

    const jsonVal = jsonEditor.getValue();
    localStorage.setItem('jsonEditorContent', jsonVal);

    if (!jsonVal.trim().startsWith('{')) return;

    try {
      isUpdating = true;
      const result = await convert(jsonVal, 'json_to_hex');
      hexEditor.setValue(result);
    } catch (e) {
      console.warn("JSON→HEX failed:", e);
    } finally {
      isUpdating = false;
    }
  });

  hexEditor.onDidChangeModelContent(async () => {
    if (!currentSchema || isUpdating) return;
    userHasEdited = true;

    const hexVal = hexEditor.getValue();
    localStorage.setItem('hexEditorContent', hexVal);

    if (!/^[0-9A-Fa-f\s]+$/.test(hexVal)) return;

    try {
      isUpdating = true;
      const result = await convert(hexVal, 'hex_to_json');
      jsonEditor.setValue(JSON.stringify(JSON.parse(result), null, 2));
    } catch (e) {
      console.warn("HEX→JSON failed:", e);
    } finally {
      isUpdating = false;
    }
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
