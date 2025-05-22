function populateDropdowns(data) {
  const l1 = document.getElementById('level1Select');
  const l2 = document.getElementById('level2Select');
  const l3 = document.getElementById('level3Select');

  l1.innerHTML = '<option value="">Select Level 1</option>';
  Object.keys(data).forEach(k => {
    if (typeof data[k] === 'object') {
      l1.innerHTML += `<option value="${k}">${k}</option>`;
    }
  });

  l1.onchange = () => {
    l2.innerHTML = '<option value="">Select Level 2</option>';
    l3.innerHTML = '<option value="">Select Level 3</option>';
    const level2Obj = data[l1.value] || {};
    Object.keys(level2Obj).forEach(k => {
      if (typeof level2Obj[k] === 'object') {
        l2.innerHTML += `<option value="${k}">${k}</option>`;
      }
    });
  };

  l2.onchange = () => {
    l3.innerHTML = '<option value="">Select Level 3</option>';
    const level3Obj = (data[l1.value] || {})[l2.value] || {};
    Object.keys(level3Obj).forEach(k => {
      if (Array.isArray(level3Obj[k])) {
        l3.innerHTML += `<option value="${k}">${k}</option>`;
      }
    });
  };

  l3.onchange = () => {
    const level3Obj = (data[l1.value] || {})[l2.value] || {};
    const selectedArray = level3Obj[l3.value];
    if (!loadedTestcase && Array.isArray(selectedArray)) {
      const existingIds = selectedArray.map(t => t.id || '');
      let maxBase = 0;
      existingIds.forEach(id => {
        const match = id.match(/^TC(\d+)/i);
        if (match) {
          const num = parseInt(match[1]);
          if (!isNaN(num) && num > maxBase) maxBase = num;
        }
      });
      document.getElementById('saveId').value = `TC${maxBase + 1}`;
    }
  };
}
