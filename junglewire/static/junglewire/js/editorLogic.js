const testcaseData = JSON.parse(document.getElementById('testcase-data').textContent);
let monacoEditor;
let loadedTestcase = null;

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
  }

  buildTree(testcaseData, document.getElementById('testcaseTree'));
});

function validateEditorJSON() {
  const saveBtn = document.getElementById('saveBtn');
  try {
    JSON.parse(monacoEditor.getValue());
    saveBtn.classList.remove('disabled');
    saveBtn.title = "Save Test Case";
  } catch {
    saveBtn.classList.add('disabled');
    saveBtn.title = "Invalid JSON – cannot save";
  }
}
