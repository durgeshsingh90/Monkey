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
    const json = await response.json();
    return json.hex ?? json;
  }

  async function convertHexToJson(hexString) {
    if (!/^[0-9A-F]+$/i.test(hexString)) return;

    try {
      isUpdating = true;
      const result = await convert(hexString, 'hex_to_json');
      let finalJson = JSON.stringify(result, null, 2);

      const mango = document.getElementById('mango-toggle');
      if (mango && mango.checked) {
        finalJson = applyMangoConversion(finalJson);
      }

      jsonEditor.setValue(finalJson);
      localStorage.setItem('jsonEditorContent', finalJson);
    } catch (e) {
      console.warn("HEX→JSON conversion failed:", e);
    } finally {
      isUpdating = false;
    }
  }

  function applyMangoConversion(jsonStr) {
    try {
      const obj = JSON.parse(jsonStr);
      const targetKeys = ['mti', 'DE004', 'DE048'];

      function convertNumbers(o) {
        for (const key in o) {
          if (typeof o[key] === 'object' && o[key] !== null) {
            convertNumbers(o[key]);
          } else if (targetKeys.includes(key) && typeof o[key] === 'string' && /^\d+$/.test(o[key])) {
            o[key] = Number(o[key]);
          }
        }
      }

      convertNumbers(obj);
      return JSON.stringify(obj, null, 2);
    } catch (e) {
      console.warn("Mango conversion failed:", e);
      return jsonStr;
    }
  }

  function extractHexFromLog(raw) {
    const hexLines = raw
      .split('\n')
      .filter(line => /^[\s\dA-F]{4,}\s+([0-9A-Fa-f]{2}\s+)+/.test(line))
      .map(line => {
        const match = line.match(/^\s*\S+\s+((?:[0-9A-Fa-f]{2}\s+)+)/);
        return match ? match[1].replace(/\s+/g, '') : '';
      })
      .filter(Boolean);

    return hexLines.join('').toUpperCase();
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
            let parsed = JSON.stringify(result, null, 2);
            if (document.getElementById('mango-toggle')?.checked) {
              parsed = applyMangoConversion(parsed);
            }
            setModelValueSafely(jsonEditor, parsed);
          }
        } catch (err) {
          console.warn("Conversion failed:", err);
        }
      };

      schemaButtonsContainer.appendChild(btn);
    });

    const savedSchema = localStorage.getItem('selectedSchema');
    if (savedSchema) {
      const savedButton = [...document.querySelectorAll('.schema-btn')]
        .find(btn => btn.dataset.schema === savedSchema);
      if (savedButton) {
        savedButton.classList.add('active');
        currentSchema = savedSchema;

        if (savedHex && savedSchema === 'omnipay.json') {
          const cleanedHex = savedHex.replace(/\s+/g, '').toUpperCase();
          if (/^[0-9A-F]+$/.test(cleanedHex)) {
            convertHexToJson(cleanedHex);
          }
        }
      }
    }
  }

  jsonEditor.onDidChangeModelContent(async () => {
    if (!currentSchema || isUpdating) return;
    userHasEdited = true;

    const jsonVal = jsonEditor.getValue().trim();
    localStorage.setItem('jsonEditorContent', jsonVal);

    if (!jsonVal) {
      hexEditor.setValue('');
      localStorage.setItem('hexEditorContent', '');
      return;
    }

    try {
      isUpdating = true;
      const result = await convert(jsonVal, 'json_to_hex');
      hexEditor.setValue(result);
      localStorage.setItem('hexEditorContent', result);
    } catch (e) {
      console.warn("JSON→HEX failed:", e);
    } finally {
      isUpdating = false;
    }
  });

  hexEditor.onDidChangeModelContent(async () => {
    if (!currentSchema || isUpdating) return;
    userHasEdited = true;

    let hexVal = hexEditor.getValue().trim();
    let cleanedHex;

    if (!hexVal) {
      jsonEditor.setValue('');
      localStorage.setItem('jsonEditorContent', '');
      return;
    }

    if (/^\s*\d{4}\s+[0-9A-Fa-f]{2}/m.test(hexVal)) {
      cleanedHex = extractHexFromLog(hexVal);
    } else {
      cleanedHex = hexVal.replace(/\s+/g, '').toUpperCase();
    }

    if (hexVal !== cleanedHex) {
      isUpdating = true;
      hexEditor.setValue(cleanedHex);
      isUpdating = false;

      setTimeout(() => convertHexToJson(cleanedHex), 0);
      return;
    }

    localStorage.setItem('hexEditorContent', cleanedHex);
    convertHexToJson(cleanedHex);
  });

  document.getElementById('mango-toggle').addEventListener('change', () => {
    if (!currentSchema || !jsonEditor.getValue().trim()) return;
    try {
      const updated = applyMangoConversion(jsonEditor.getValue());
      jsonEditor.setValue(updated);
    } catch (e) {
      console.warn("Mango toggle failed:", e);
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
