function populateDropdownsFromFiles(fileTreeMap) {
  const fileSelect = document.getElementById('fileSelect');
  const rootSelect = document.getElementById('rootSelect');

  fileSelect.innerHTML = '<option value="">Select File</option>';
  rootSelect.innerHTML = '<option value="">Select Root</option>';

  // Populate filenames
  Object.keys(fileTreeMap).forEach(filename => {
    const option = document.createElement('option');
    option.value = filename;
    option.textContent = filename;
    fileSelect.appendChild(option);
  });

  // When a file is selected, populate roots
  fileSelect.addEventListener('change', () => {
    const selectedFile = fileSelect.value;
    rootSelect.innerHTML = '<option value="">Select Root</option>';

    if (selectedFile && fileTreeMap[selectedFile]) {
      const roots = fileTreeMap[selectedFile];
      roots.forEach(root => {
        const opt = document.createElement('option');
        opt.value = root;
        opt.textContent = root;
        rootSelect.appendChild(opt);
      });
    }
  });

}
