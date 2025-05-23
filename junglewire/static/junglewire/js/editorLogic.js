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
    });
  validateEditorJSON(); // Call once on load
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
