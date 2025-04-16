// Initialize CodeMirror
var editor = CodeMirror.fromTextArea(document.getElementById('code-editor'), {
    lineNumbers: true,
    mode: 'javascript', // Set to the mode you need
    theme: 'monokai', // Choose a theme, optional
    keyMap: 'sublime', // KeyMap, optional
    tabSize: 2,
    indentWithTabs: true,
});

// Load saved data from localStorage if it exists
if (localStorage.getItem('editorContent')) {
    editor.setValue(localStorage.getItem('editorContent'));
}

// Update status bar
function updateStatusBar() {
    const totalLines = editor.lineCount();
    const selectedText = editor.getSelection();
    const selectedLength = selectedText.length;

    document.getElementById('total-lines').textContent = `Total lines: ${totalLines}`;
    document.getElementById('selected-length').textContent = `Selected text length: ${selectedLength}`;
}

// Save data to localStorage on changes
editor.on('changes', function() {
    localStorage.setItem('editorContent', editor.getValue());
    updateStatusBar();
});

// Update status bar on cursor activity
editor.on('cursorActivity', updateStatusBar);

// Initialize the status bar
updateStatusBar();
