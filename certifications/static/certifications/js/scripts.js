console.log("🧪 Handsontable global object:", window.Handsontable);

window.addEventListener('load', () => {
  // Delay check until all resources have loaded
  setTimeout(() => {
    if (typeof Handsontable === 'undefined') {
      console.error("❌ Handsontable is not loaded.");
      return;
    }

    console.log("✅ Handsontable is loaded.");

    let editor, hot;
    let currentRqMsgs = [];

    require.config({ paths: { 'vs': 'https://cdn.jsdelivr.net/npm/monaco-editor@0.38.0/min/vs' } });
    require(["vs/editor/editor.main"], function () {
      editor = monaco.editor.create(document.getElementById('json-editor'), {
        value: '',
        language: 'json',
        theme: 'vs-dark',
        automaticLayout: true
      });

      fetch('/certifications/get_structure/')
        .then(res => res.json())
        .then(data => renderTree(data));
    });

    function renderTree(data) {
      const container = document.getElementById('tree-container');
      container.innerHTML = '';
      const requests = data.requests;
      const openUsers = JSON.parse(localStorage.getItem('openUsers') || '[]');

      for (const user in requests) {
        const userWrapper = document.createElement('div');
        const isOpen = openUsers.includes(user);
        const toggleText = isOpen ? '➖' : '➕';
        userWrapper.innerHTML = `<span style="cursor:pointer;" onclick="toggleCollapse(this, '${user}')">${toggleText} ${user}</span>`;
        const tcList = document.createElement('ul');
        tcList.style.display = isOpen ? 'block' : 'none';

        for (const testcase in requests[user]) {
          const tcEl = document.createElement('li');
          tcEl.innerHTML = `
            <label style="cursor:pointer;">
              <input type="checkbox" class="testcase-checkbox" data-user="${user}" data-testcase="${testcase}" onchange="updateSelectedData()">
              🧪 <span class="testcase" data-user="${user}" data-testcase="${testcase}">${testcase}</span>
            </label>
          `;
          tcEl.querySelector('.testcase').addEventListener('click', (e) => {
            const user = e.target.dataset.user;
            const testcase = e.target.dataset.testcase;
            fetch(`/certifications/get_testcase_data/?user=${encodeURIComponent(user)}&testcase=${encodeURIComponent(testcase)}`)
              .then(res => res.json())
              .then(tcData => {
                const rqMsgs = tcData.rq_msgs || [];
                let content = '';

                if (typeof rqMsgs[0] === 'string') {
                  content = rqMsgs.join('\n\n');
                  editor.updateOptions({ language: 'plaintext' });
                } else {
                  content = JSON.stringify(rqMsgs, null, 2);
                  editor.updateOptions({ language: 'json' });
                }

                editor.setValue(content);
                currentRqMsgs = rqMsgs;
                document.getElementById('selected-tests').innerText = `Selected: ${testcase}`;
                document.getElementById('grid-view').style.display = 'none';
                document.getElementById('json-editor').style.display = 'block';
                document.getElementById('toggle-view').innerText = 'Switch to Grid View';
              });
          });
          tcList.appendChild(tcEl);
        }

        userWrapper.appendChild(tcList);
        container.appendChild(userWrapper);
      }
    }

    window.toggleCollapse = function (el, user) {
      const ul = el.parentElement.querySelector('ul');
      let openUsers = JSON.parse(localStorage.getItem('openUsers') || '[]');

      if (ul.style.display === 'none') {
        ul.style.display = 'block';
        el.innerHTML = el.innerHTML.replace('➕', '➖');
        if (!openUsers.includes(user)) openUsers.push(user);
      } else {
        ul.style.display = 'none';
        el.innerHTML = el.innerHTML.replace('➖', '➕');
        openUsers = openUsers.filter(u => u !== user);
      }

      localStorage.setItem('openUsers', JSON.stringify(openUsers));
    };

    document.getElementById('collapse-toggle').addEventListener('click', () => {
      const container = document.getElementById('tree-container');
      const allToggles = container.querySelectorAll('span[onclick^="toggleCollapse"]');
      const expanding = document.getElementById('collapse-toggle').innerText === '➕';
      let openUsers = [];

      allToggles.forEach(toggle => {
        const ul = toggle.parentElement.querySelector('ul');
        const user = toggle.textContent.trim().substring(2);
        if (expanding) {
          ul.style.display = 'block';
          toggle.innerHTML = toggle.innerHTML.replace('➕', '➖');
          openUsers.push(user);
        } else {
          ul.style.display = 'none';
          toggle.innerHTML = toggle.innerHTML.replace('➖', '➕');
        }
      });

      document.getElementById('collapse-toggle').innerText = expanding ? '➖' : '➕';
      localStorage.setItem('openUsers', JSON.stringify(expanding ? openUsers : []));
    });

    window.updateSelectedData = async function () {
      const checkboxes = document.querySelectorAll('.testcase-checkbox:checked');
      const selected = Array.from(checkboxes).map(cb => ({
        user: cb.dataset.user,
        testcase: cb.dataset.testcase
      }));

      if (selected.length === 0) {
        editor.setValue('');
        document.getElementById('selected-tests').innerText = '';
        currentRqMsgs = [];
        return;
      }

      const selectedNames = selected.map(s => s.testcase).join(', ');
      document.getElementById('selected-tests').innerText = `Selected: ${selectedNames}`;

      let allRqMsgs = [];

      for (const sel of selected) {
        const res = await fetch(`/certifications/get_testcase_data/?user=${encodeURIComponent(sel.user)}&testcase=${encodeURIComponent(sel.testcase)}`);
        const tcData = await res.json();
        if (Array.isArray(tcData.rq_msgs)) {
          allRqMsgs = allRqMsgs.concat(tcData.rq_msgs);
        }
      }

      currentRqMsgs = allRqMsgs;

      let content;
      if (typeof allRqMsgs[0] === 'string') {
        content = allRqMsgs.join('\n\n');
        editor.updateOptions({ language: 'plaintext' });
      } else {
        content = JSON.stringify(allRqMsgs, null, 2);
        editor.updateOptions({ language: 'json' });
      }

      editor.setValue(content);

      if (document.getElementById('grid-view').style.display === 'block') {
        loadGrid(allRqMsgs);
      }
    };

    document.getElementById('toggle-view').addEventListener('click', function () {
      const grid = document.getElementById('grid-view');
      const jsonEditor = document.getElementById('json-editor');

      if (grid.style.display === 'none') {
        if (!Array.isArray(currentRqMsgs) || currentRqMsgs.length === 0) {
          alert("No valid rq_msgs to display in grid.");
          return;
        }

        grid.style.display = 'block';
        jsonEditor.style.display = 'none';
        this.innerText = 'Switch to JSON View';
        loadGrid(currentRqMsgs);
      } else {
        grid.style.display = 'none';
        jsonEditor.style.display = 'block';
        this.innerText = 'Switch to Grid View';
      }
    });

    function flattenDataElements(msg) {
      const flat = { mti: msg.mti };
      const de = msg.data_elements || {};
      for (const key in de) {
        if (typeof de[key] === 'object' && !Array.isArray(de[key])) {
          for (const subKey in de[key]) {
            flat[`${key}.${subKey}`] = de[key][subKey];
          }
        } else {
          flat[key] = de[key];
        }
      }
      return flat;
    }

    function loadGrid(rqMsgs) {
      if (typeof Handsontable === 'undefined') {
        alert("Handsontable is not loaded.");
        return;
      }

      const container = document.getElementById('grid-view');
      if (hot) hot.destroy();

      const allHeaders = new Set();
      const flattenedData = rqMsgs.map(msg => {
        const flat = flattenDataElements(msg);
        Object.keys(flat).forEach(k => allHeaders.add(k));
        return flat;
      });

      const sortedHeaders = Array.from(allHeaders).sort();

      hot = new Handsontable(container, {
        data: flattenedData,
        colHeaders: sortedHeaders,
        columns: sortedHeaders.map(k => ({ data: k })),
        stretchH: 'all',
        autoWrapRow: true,
        rowHeaders: true,
        height: '80vh',
        licenseKey: 'non-commercial-and-evaluation'
      });
    }
  }, 0); // End of setTimeout
});
