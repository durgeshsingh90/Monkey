let selectedFolderPath = [];  // e.g., ["certified", "Fiserv", "Authorization Tests"]
const deleteGif = "/static/junglewire/images/delete.gif";
const deletePng = "/static/junglewire/images/delete.png";

const hexInput = document.getElementById('hexInput');
const lineNumbers = document.getElementById('lineNumbers');
const lineNumbersWrapper = document.getElementById('lineNumbersWrapper');

function updateLineNumbers() {
  const lineCount = hexInput.value.split('\n').length;
  lineNumbers.textContent = Array.from({ length: lineCount }, (_, i) => i + 1).join('\n');
}

hexInput.addEventListener('input', updateLineNumbers);
hexInput.addEventListener('scroll', () => {
  lineNumbersWrapper.scrollTop = hexInput.scrollTop;
});
updateLineNumbers();

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
