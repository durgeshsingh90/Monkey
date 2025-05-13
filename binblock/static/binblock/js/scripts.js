require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.32.1/min/vs' } });
require(['vs/editor/editor.main'], function () {
    var editor = monaco.editor.create(document.getElementById('editor'), {
        value: '',
        language: 'plaintext',
        theme: 'vs-dark'
    });

    var editorReadOnly = monaco.editor.create(document.getElementById('editor-readonly'), {
        value: '',
        language: 'sql',
        theme: 'vs-dark',
        readOnly: true
    });

    var editorEditable = monaco.editor.create(document.getElementById('editor-container'), {
        value: '',
        language: 'json',
        theme: 'vs-dark'
    });

    // Load content for editable editor
    fetch('/get_content/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            if (Object.keys(data.content).length === 0) {
                editorEditable.setValue(''); // Set container 3 editor to blank if content is empty
            } else {
                editorEditable.setValue(JSON.stringify(data.content, null, 2));
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            editorEditable.setValue('Failed to load content');
        });

    function updateContainer3() {
        fetch('/get_content/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            })
            .then(data => {
                if (Object.keys(data.content).length === 0) {
                    editorEditable.setValue(''); // Set container 3 editor to blank if content is empty
                } else {
                    editorEditable.setValue(JSON.stringify(data.content, null, 2));
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                editorEditable.setValue('Failed to load content');
            });
    }

    document.getElementById('cleanDataBtn').addEventListener('click', function () {
        var content = editor.getValue();
        var lines = content.split('\n');
        var cleanedLines = Array.from(new Set(
            lines.filter(line => line.trim() !== '').map(Number)
        )).sort((a, b) => a - b);
        editor.setValue(cleanedLines.join('\n'));
        editorReadOnly.setValue(cleanedLines.join('\n')); // Update read-only editor

        var cleanDataBtn = document.getElementById('cleanDataBtn');
        cleanDataBtn.textContent = 'Cleaned';
        cleanDataBtn.classList.add('cleaned');

        setTimeout(function () {
            cleanDataBtn.textContent = 'Clean Data';
            cleanDataBtn.classList.remove('cleaned');
            editor.setScrollTop(0); // Scroll to the top
        }, 1000);
    });

    document.getElementById('copyBtn').addEventListener('click', function () {
        var copyBtn = document.getElementById('copyBtn');
        var content = editorReadOnly.getValue();
        navigator.clipboard.writeText(content).then(function () {
            copyBtn.textContent = 'Copied';
            copyBtn.classList.add('copied');
            setTimeout(function () {
                copyBtn.textContent = 'Copy';
                copyBtn.classList.remove('copied');
            }, 1000);
        });
    });

    document.getElementById('downloadBtn').addEventListener('click', function () {
        var content = editorReadOnly.getValue();
        var selectedFormat = document.querySelector('.right-buttons .selected').id;
        var fileName = selectedFormat === 'jsonBtn' ? 'output.json' : 'output.sql';
        var blob = new Blob([content], { type: 'text/plain' });
        var url = window.URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    });

    document.getElementById('jsonBtn').addEventListener('click', function () {
        setActiveFileButton('jsonBtn');
        loadFileContent('output.json');
    });

    document.getElementById('sqlBtn').addEventListener('click', function () {
        setActiveFileButton('sqlBtn');
        loadFileContent('output.sql');
    });

    function setActiveFileButton(activeBtnId) {
        document.getElementById('jsonBtn').classList.remove('selected');
        document.getElementById('sqlBtn').classList.remove('selected');
        document.getElementById(activeBtnId).classList.add('selected');
    }

    function loadFileContent(fileName) {
        // Mock file reading logic. Replace with actual file reading logic.
        if (fileName === 'output.json') {
            editorReadOnly.setValue(`{\n  "message": "This is JSON content."\n}`);
        } else if (fileName === 'output.sql') {
            editorReadOnly.setValue("SELECT * FROM table;");
        }
    }

    document.getElementById('dropdown1').addEventListener('change', function (event) {
        var form = document.getElementById('queryForm');
        updateContainer3(); // Fetch and update container 3
        form.submit();
    });

    document.getElementById('fileUpload').addEventListener('change', function () {
        var dropdown1 = document.getElementById('dropdown1');
        dropdown1.disabled = true;

        // Display the full name of the uploaded file
        var fileDisplay = document.getElementById('fileDisplay');
        var file = document.getElementById('fileUpload').files[0];
        if (file) {
            fileDisplay.style.display = 'block';
            fileDisplay.textContent = file.name;
        }
        updateContainer3();
    });

    document.getElementById('queryForm').addEventListener('submit', function (event) {
        event.preventDefault(); // Prevent default form submission
        var formData = new FormData(this);
        
        fetch(this.action, {
            method: 'POST',
            body: formData
        }).then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok ' + response.statusText);
            }
            return response.json();
        }).then(data => {
            updateContainer3(); // Update content after form submission
        }).catch(error => {
            console.error('Fetch error:', error);
        });
    });
});
