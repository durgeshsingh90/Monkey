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
    updateContainer3();

function updateContainer3() {
fetch('/binblock/get_content/')
        .then(response => {
            if (!response.ok) {
                // Likely 404 – block_content.json not created yet
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


    document.getElementById('cleanDataBtn').addEventListener('click', function () {
        var content = editor.getValue();
        var lines = content.split('\n');
        var cleanedLines = Array.from(new Set(
            lines.filter(line => line.trim() !== '').map(Number)
        )).sort((a, b) => a - b);
        editor.setValue(cleanedLines.join('\n'));
        editorReadOnly.setValue(cleanedLines.join('\n'));

        var cleanDataBtn = document.getElementById('cleanDataBtn');
        cleanDataBtn.textContent = 'Cleaned';
        cleanDataBtn.classList.add('cleaned');

        setTimeout(function () {
            cleanDataBtn.textContent = 'Clean Data';
            cleanDataBtn.classList.remove('cleaned');
            editor.setScrollTop(0);
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
    fetch(`/media/binblock/${fileName}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load ${fileName}`);
            }
            return response.text();
        })
        .then(data => {
            editorReadOnly.setValue(data);
        })
        .catch(err => {
            editorReadOnly.setValue(`// Error loading ${fileName}`);
            console.error(err);
        });
}

document.getElementById('dropdown1').addEventListener('change', function () {
    const formData = new FormData();
    const selectedDb = this.value;

    formData.append('dropdown1', selectedDb);

    showLoading();  // 👈 Show loading screen

    fetch('/binblock/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Server error: ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        console.log("✅ DB query completed:", data);
        updateContainer3();
    })
    .catch(error => {
        console.error('❌ Error running DB query:', error);
    })
    .finally(() => {
        hideLoading();  // 👈 Hide when done
    });
});




document.getElementById('fileUpload').addEventListener('change', function () {
    const file = this.files[0];
    const dropdown1 = document.getElementById('dropdown1');
    dropdown1.disabled = true;

    const fileDisplay = document.getElementById('fileDisplay');

    if (file) {
        showLoading();  // 👈 Show loading

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

                    // ❗ Blank out LOWBIN / HIGHBIN if present
                    firstEntry['LOWBIN'] = '';
                    firstEntry['HIGHBIN'] = '';

                    editorEditable.setValue(JSON.stringify(firstEntry, null, 2));
                } catch (e) {
                    console.error('Invalid JSON file:', e);
                    editorEditable.setValue('// Invalid JSON file');
                } finally {
                    hideLoading();  // 👈 Hide loading even on error
                }
            };
            reader.readAsText(file);
        } else {
            hideLoading();
        }
    } else {
        fileDisplay.style.display = 'none';
        fileDisplay.textContent = '';
        hideLoading();
    }
});


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

const dbDropdown = document.getElementById('dropdown1');
const fileInput = document.getElementById('fileUpload');

// When a database is selected, disable file input
dbDropdown.addEventListener('change', function () {
    if (this.value) {
        fileInput.disabled = true;
    } else {
        fileInput.disabled = false;
    }
});

// When a file is selected, disable dropdown
fileInput.addEventListener('change', function () {
    if (this.files.length > 0) {
        dbDropdown.disabled = true;
    } else {
        dbDropdown.disabled = false;
    }
});
});

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

document.getElementById('generateBtn').addEventListener('click', function () {
    const editorContent = editor.getValue();              // BIN list from Container 1
    const editedJson = editorEditable.getValue();         // Edited JSON from Container 3

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
        editorReadOnly.setValue(JSON.stringify(data.generated, null, 2));  // Show in Container 4
    })
    .catch(err => {
        console.error('Generate error:', err);
        editorReadOnly.setValue('// Error generating output.');
    })
    .finally(() => {
        hideLoading();
    });
});
