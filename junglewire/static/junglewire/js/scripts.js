    // Exclusive group logic
    const exclusiveButtons = [
      'dev77', 'paypal77', 'novate', 'test77', 'cert77', 'netscaler'
    ];
    exclusiveButtons.forEach(id => {
      document.getElementById(id).addEventListener('click', function () {
        exclusiveButtons.forEach(btnId => {
          document.getElementById(btnId).classList.remove('active');
        });
        this.classList.add('active');
      });
    });

    // Independent toggles
    ['updateBtn', 'echoBtn', 'incrBtn'].forEach(id => {
      document.getElementById(id).addEventListener('click', function () {
        this.classList.toggle('active');
      });
    });

    // Monaco setup
    require.config({ paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' } });
    require(['vs/editor/editor.main'], function () {
      monaco.editor.create(document.getElementById('editor'), {
        value: `{\n  "example": true\n}`,
        language: 'json',
        theme: 'vs-light',
        automaticLayout: true
      });
    });

    // Copy & Clear behavior
    const copyBtn = document.getElementById('copyBtn');
    const clearBtn = document.getElementById('clearBtn');
    const logViewer = document.getElementById('logViewer');

    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(logViewer.value).then(() => {
        const original = copyBtn.textContent;
        copyBtn.textContent = "Copied";
        setTimeout(() => copyBtn.textContent = original, 1000);
      });
    });

    clearBtn.addEventListener('click', () => {
      logViewer.value = '';
      const original = clearBtn.textContent;
      clearBtn.textContent = "Cleared";
      setTimeout(() => clearBtn.textContent = original, 1000);
    });

    // Simulated log appending (you can replace this with live backend feed)
    /*
    setInterval(() => {
      logViewer.value += `\n[${new Date().toLocaleTimeString()}] Log entry`;
      logViewer.scrollTop = logViewer.scrollHeight;
    }, 3000);
    */