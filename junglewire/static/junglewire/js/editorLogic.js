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

    monacoEditor.onDidChangeModelContent(() => {
      validateEditorJSON();
      convertJsonToHexLive(); // 👈 add this line!
    });

    validateEditorJSON();
    convertJsonToHexLive(); // 👈 call once at load
  }
});


function validateEditorJSON() {
  const saveBtn = document.getElementById('saveConfirmBtn');
  if (!saveBtn) return; // Prevent null crash

  try {
    JSON.parse(monacoEditor.getValue());
    saveBtn.classList.remove('disabled');
    saveBtn.disabled = false;
    saveBtn.title = "Save Test Case";
  } catch {
    saveBtn.classList.add('disabled');
    saveBtn.disabled = true;
    saveBtn.title = "Invalid JSON – cannot save";
  }
}

function convertJsonToHexLive() {
  let jsonText = "";
  let parsed;

  try {
    jsonText = monacoEditor.getValue();
    parsed = JSON.parse(jsonText);
  } catch (err) {
    const hexField = document.getElementById('hexInput');
    if (hexField) {
      hexField.value = `❌ Invalid JSON:\n${err.message}`;
      updateLineNumbers();
    }
    console.warn("Invalid JSON — skipping conversion.", err.message);
    return;
  }

  const payloads = Array.isArray(parsed) ? parsed : [parsed];
  const hexOutput = [];

  const promises = payloads.map((payload, idx) => {
    const mti = payload?.mti || "0200";
    const fullPayload = {
      mti: mti,
      data_elements: payload.data_elements || {}
    };

    return fetch('/hex2iso/convert/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify({
        direction: 'json_to_hex',
        schema: 'omnipay.json',
        input: JSON.stringify(fullPayload)
      })
    })
    .then(res => {
      if (!res.ok) {
        return res.json().then(err => Promise.reject(err));
      }
      return res.json();
    })
    .then(data => {
      if (data.hex) {
        console.log(`✅ HEX result for item ${idx + 1}:`, data.hex);
        hexOutput.push(data.hex);
      } else {
        hexOutput.push(`❌ ERROR in item ${idx + 1}: No HEX returned`);
      }
    })
    .catch(err => {
      const msg = err?.error || JSON.stringify(err) || 'Unknown error';
      console.error(`❌ HEX conversion failed for item ${idx + 1}:`, msg);
      hexOutput.push(`❌ ERROR in item ${idx + 1}:\n${msg}`);
    });
  });

  Promise.all(promises).then(() => {
    const hexField = document.getElementById('hexInput');
    if (hexField) {
      hexField.value = hexOutput.join('\n\n');
      updateLineNumbers();
    }
  });
}
