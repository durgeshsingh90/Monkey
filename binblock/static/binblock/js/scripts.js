let editor, editorReadOnly, editorEditable;

require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.32.1/min/vs' } });

require(['vs/editor/editor.main'], function () {
    editor = monaco.editor.create(document.getElementById('editor'), {
        value: '',
        language: 'plaintext',
        theme: 'vs-dark'
    });

    editorReadOnly = monaco.editor.create(document.getElementById('editor-readonly'), {
        value: '',
        language: 'sql',
        theme: 'vs-dark',
        readOnly: true
    });

    editorEditable = monaco.editor.create(document.getElementById('editor-container'), {
        value: '',
        language: 'json',
        theme: 'vs-dark'
    });

    updateContainer3();

    document.getElementById('cleanDataBtn').addEventListener('click', function () {
        const content = editor.getValue();
        const lines = content.split('\n');
        const cleanedLines = Array.from(new Set(
            lines.filter(line => line.trim() !== '').map(Number)
        )).sort((a, b) => a - b);
        editor.setValue(cleanedLines.join('\n'));
        editorReadOnly.setValue(cleanedLines.join('\n'));

        const cleanBtn = document.getElementById('cleanDataBtn');
        cleanBtn.textContent = 'Cleaned';
        cleanBtn.classList.add('cleaned');

        setTimeout(() => {
            cleanBtn.textContent = 'Clean Data';
            cleanBtn.classList.remove('cleaned');
            editor.setScrollTop(0);
        }, 1000);
    });

    document.getElementById('copyBtn').addEventListener('click', function () {
        const content = editorReadOnly.getValue();
        navigator.clipboard.writeText(content).then(() => {
            const btn = document.getElementById('copyBtn');
            btn.textContent = 'Copied';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.textContent = 'Copy';
                btn.classList.remove('copied');
            }, 1000);
        });
    });

    document.getElementById('downloadBtn').addEventListener('click', function () {
        const content = editorReadOnly.getValue();
        const selectedFormat = document.querySelector('.right-buttons .selected').id;
        const fileName = selectedFormat === 'jsonBtn' ? 'output.json' : 'output.sql';
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        URL.revokeObjectURL(url);
        a.remove();
    });

    document.getElementById('jsonBtn').addEventListener('click', function () {
        setActiveFileButton('jsonBtn');
        loadFileContent('generated_output.json');
    });

    document.getElementById('sqlBtn').addEventListener('click', function () {
        setActiveFileButton('sqlBtn');
        loadFileContent('generated_output.sql');
    });

    function setActiveFileButton(activeBtnId) {
        document.getElementById('jsonBtn').classList.remove('selected');
        document.getElementById('sqlBtn').classList.remove('selected');
        document.getElementById(activeBtnId).classList.add('selected');
    }

    function loadFileContent(fileName) {
        fetch(`/media/binblock/${fileName}`)
            .then(response => {
                if (!response.ok) throw new Error(`Failed to load ${fileName}`);
                return response.text();
            })
            .then(data => editorReadOnly.setValue(data))
            .catch(err => {
                editorReadOnly.setValue(`// Error loading ${fileName}`);
                console.error(err);
            });
    }

    function updateContainer3() {
        fetch('/binblock/get_content/')
            .then(response => {
                if (!response.ok) {
                    editorEditable.setValue('');
                    return null;
                }
                return response.json();
            })
            .then(data => {
                if (data && data.content) {
                    editorEditable.setValue(JSON.stringify(data.content, null, 2));
                } else {
                    editorEditable.setValue('');
                }
            })
            .catch(error => {
                console.warn('Optional fetch warning:', error);
                editorEditable.setValue('');
            });
    }

    document.getElementById('dropdown1').addEventListener('change', function () {
        const formData = new FormData();
        const selectedDb = this.value;
        formData.append('dropdown1', selectedDb);

        showLoading();

        fetch('/binblock/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => {
            if (!response.ok) throw new Error('Server error: ' + response.statusText);
            return response.json();
        })
        .then(data => {
            updateContainer3();
        })
        .catch(error => {
            console.error('❌ Error running DB query:', error);
        })
        .finally(() => {
            hideLoading();
        });
    });

    document.getElementById('fileUpload').addEventListener('change', function () {
        const file = this.files[0];
        const dropdown1 = document.getElementById('dropdown1');
        dropdown1.disabled = true;

        const fileDisplay = document.getElementById('fileDisplay');

        if (file) {
            showLoading();
            fileDisplay.style.display = 'block';
            fileDisplay.textContent = file.name;

            if (file.name.endsWith('.json')) {
                const reader = new FileReader();
                reader.onload = function (event) {
                    try {
                        const content = JSON.parse(event.target.result);
                        let firstEntry = {};
                        if (Array.isArray(content) && content.length > 0) {
                            firstEntry = content[0];
                        } else if (typeof content === 'object') {
                            firstEntry = content;
                        }

                        firstEntry['LOWBIN'] = '';
                        firstEntry['HIGHBIN'] = '';
                        editorEditable.setValue(JSON.stringify(firstEntry, null, 2));
                    } catch (e) {
                        console.error('Invalid JSON file:', e);
                        editorEditable.setValue('// Invalid JSON file');
                    } finally {
                        hideLoading();
                    }
                };
                reader.readAsText(file);
            } else {
                hideLoading();
            }
        } else {
            fileDisplay.style.display = 'none';
            fileDisplay.textContent = '';
            dropdown1.disabled = false;
        }
    });

    // Handle exclusive selection (dropdown vs. file)
    const dbDropdown = document.getElementById('dropdown1');
    const fileInput = document.getElementById('fileUpload');

    dbDropdown.addEventListener('change', function () {
        fileInput.disabled = !!this.value;
    });

    fileInput.addEventListener('change', function () {
        dbDropdown.disabled = this.files.length > 0;
    });

    document.getElementById('generateBtn').addEventListener('click', function () {
        const editorContent = editor.getValue();              // From Container 1
        const editedJson = editorEditable.getValue();         // From Container 3

        showLoading();

        fetch('/binblock/generate_output/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                bin_list: editorContent.split('\n').filter(line => line.trim() !== ''),
                edited_bin: JSON.parse(editedJson)
            })
        })
        .then(res => res.json())
        .then(data => {
            loadFileContent('generated_output.json');
        })
        .catch(err => {
            console.error('Generate error:', err);
            editorReadOnly.setValue('// Error generating output.');
        })
        .finally(() => {
            hideLoading();
        });
    });
});

// CSRF helper
function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith(name + '=')) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return '';
}

// Loading overlay
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = 'flex';
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.style.display = 'none';
}
