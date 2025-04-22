const excelInput = document.getElementById('excelFile');
const logInput = document.getElementById('logFile');
const excelDropZone = document.getElementById('excelDropZone');
const logDropZone = document.getElementById('logDropZone');
const status = document.getElementById('status');
const result = document.getElementById('result');
const resultContent = document.getElementById('resultContent');
const excelCheck = document.getElementById('excelCheck');
const logCheck = document.getElementById('logCheck');
const spinner = document.getElementById('spinner');

function disableDropZones() {
    excelDropZone.classList.add('opacity-50', 'pointer-events-none');
    logDropZone.classList.add('opacity-50', 'pointer-events-none');
}

function scrollToResult() {
    result.scrollIntoView({ behavior: 'smooth' });
}

async function processFiles(excelFile, logFile) {
    if (!excelFile || !logFile) {
        status.innerHTML = '<p class="text-red-600">Please upload both Excel and Log files.</p>';
        return;
    }

    status.innerHTML = '<p class="text-blue-600">Uploading and processing...</p>';
    spinner.classList.remove('hidden');

    const formData = new FormData();
    formData.append('excel', excelFile);
    formData.append('log', logFile);

    try {
        const response = await fetch('/api/process-files', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        status.innerHTML = '<p class="text-green-600">Processing complete!</p>';
        result.classList.remove('hidden');
        resultContent.textContent = JSON.stringify(data, null, 2);
        disableDropZones();
        scrollToResult();
    } catch (error) {
        status.innerHTML = `<p class="text-red-600">Error: ${error.message}</p>`;
        result.classList.add('hidden');
    } finally {
        spinner.classList.add('hidden');
    }
}

excelDropZone.addEventListener('click', () => excelInput.click());
logDropZone.addEventListener('click', () => logInput.click());

excelInput.addEventListener('change', () => {
    const file = excelInput.files[0];
    if (file) {
        status.innerHTML = '<p class="text-gray-600">Excel file selected.</p>';
        excelCheck.classList.remove('hidden');
        processFiles(file, logInput.files[0]);
    }
});

logInput.addEventListener('change', () => {
    const file = logInput.files[0];
    if (file) {
        status.innerHTML = '<p class="text-gray-600">Log file selected.</p>';
        logCheck.classList.remove('hidden');
        processFiles(excelInput.files[0], file);
    }
});

function setupDrop(dropZone, input, checkIcon, validExt) {
    dropZone.addEventListener('dragover', e => {
        e.preventDefault();
        dropZone.classList.add('bg-opacity-80');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('bg-opacity-80');
    });

    dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('bg-opacity-80');
        const file = e.dataTransfer.files[0];
        if (file && validExt.some(ext => file.name.endsWith(ext))) {
            input.files = e.dataTransfer.files;
            checkIcon.classList.remove('hidden');
            processFiles(
                input.id === 'excelFile' ? file : excelInput.files[0],
                input.id === 'logFile' ? file : logInput.files[0]
            );
        } else {
            status.innerHTML = `<p class="text-red-600">Invalid file type.</p>`;
        }
    });
}

setupDrop(excelDropZone, excelInput, excelCheck, ['.xlsx', '.xls']);
setupDrop(logDropZone, logInput, logCheck, ['.log', '.txt']);

// Dark mode toggle
const darkToggle = document.getElementById('darkToggle');
darkToggle.addEventListener('change', () => {
    document.documentElement.classList.toggle('dark', darkToggle.checked);
});
