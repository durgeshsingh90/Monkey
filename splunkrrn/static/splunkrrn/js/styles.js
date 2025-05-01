const textarea = document.getElementById('inputText');
const lineNumbers = document.getElementById('lineNumbers');
const statusText = document.getElementById('statusText');
const output = document.getElementById('outputBox');
let sortByTime = false;

function toggleSortTime() {
  sortByTime = !sortByTime;
  const btn = document.getElementById('sortTimeBtn');
  btn.textContent = sortByTime ? '✔ Sort by Time' : 'Sort by Time';
  updateOutput();
}

textarea.addEventListener('input', updateEverything);
textarea.addEventListener('mouseup', updateStatus);
textarea.addEventListener('keyup', updateStatus);

function updateEverything() {
  updateLineNumbers();
  updateStatus();
  updateOutput();
}

function updateLineNumbers() {
  const lines = textarea.value.split('\n').length;
  lineNumbers.innerText = Array.from({ length: lines }, (_, i) => i + 1).join('\n');
}

function updateStatus() {
  const selection = textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
  statusText.innerText = `Selected: ${selection.length} character${selection.length !== 1 ? 's' : ''}`;
}

function stringToHex(str) {
  return Array.from(str).map(c => c.charCodeAt(0).toString(16).padStart(2, '0')).join('');
}

function hexToString(hex) {
  try {
    return hex.match(/.{2}/g).map(byte => String.fromCharCode(parseInt(byte, 16))).join('');
  } catch {
    return '[Invalid hex]';
  }
}

function transformInput(line) {
  const trimmed = line.trim();

  if (/^(AND|OR)\s+"[^"]+"$/i.test(trimmed)) return trimmed;
  if (/^"[^"]+"$/.test(trimmed)) return `OR ${trimmed}`;
  if (/^\d{12}$/.test(trimmed)) return `${trimmed} OR ${stringToHex(trimmed)}`;
  if (/^[0-9a-fA-F]{24}$/.test(trimmed)) return `${trimmed} OR ${hexToString(trimmed)}`;
  return null;
}

function updateOutput() {
const lines = textarea.value.split('\n');
const transformedValues = [];

for (let i = 0; i < lines.length; i++) {
const line = lines[i].trim();
if (!line) continue;

const lastItem = transformedValues[transformedValues.length - 1];

if (/^\d{12}$/.test(line)) {
  transformedValues.push(line);
  transformedValues.push('OR');
  transformedValues.push(stringToHex(line));
  transformedValues.push('OR');
} else if (/^[0-9a-fA-F]{24}$/.test(line)) {
  transformedValues.push(line);
  transformedValues.push('OR');
  transformedValues.push(hexToString(line));
  transformedValues.push('OR');
} else if (/^"[^"]+"$/.test(line)) {
  transformedValues.push(line);
  transformedValues.push('OR');
} else if (/^AND\s+"[^"]+"$/i.test(line)) {
  // Remove the trailing OR if it exists
  if (lastItem === 'OR') transformedValues.pop();
  transformedValues.push(line);
  transformedValues.push('OR');
}
}

// Clean up final OR if it exists
if (transformedValues[transformedValues.length - 1] === 'OR') {
transformedValues.pop();
}

const timeRange = document.getElementById('timeRange').value;
const eventLimit = document.getElementById('eventLimit').value;
const durationValue = document.getElementById('durationRange').value;
const groupBy = document.getElementById('groupByField').value;
const showStats = document.getElementById('statsSummary').checked;
const sortTimeOnly = document.getElementById('sortByTimeOnly').checked;
document.getElementById('durationDisplay').textContent = `> ${durationValue}ms`;

let result = `index=application_omnipay`;

if (timeRange === "today") {
result += ` earliest=@d latest=now`;
} else if (timeRange === "yesterday") {
result += ` earliest=-1d@d latest=@d`;
} else if (timeRange) {
result += ` earliest=${timeRange} latest=now`;
}

if (transformedValues.length > 0) {
result += ` ` + transformedValues.join(' ');
}

result += ` | reverse`;

const includeHosts = Array.from(document.querySelectorAll('.host-include:checked')).map(cb => `host=${cb.value}`);
const excludeHosts = Array.from(document.querySelectorAll('.host-exclude:checked')).map(cb => `host!=${cb.value}`);

if (includeHosts.length || excludeHosts.length) {
result += ` | search (`;
if (includeHosts.length) result += includeHosts.join(" OR ");
if (includeHosts.length && excludeHosts.length) result += " OR ";
if (excludeHosts.length) result += excludeHosts.join(" OR ");
result += `)`;
}

if (sortByTime || sortTimeOnly) result += ` | sort _time`;
if (durationValue > 0) result += ` | where duration > ${durationValue}`;
if (groupBy) result += ` | stats count by ${groupBy}`;
if (eventLimit) result += ` | head ${eventLimit}`;

output.textContent = result;
}

function copyText() {
const text = output.textContent;
const copyBtn = document.getElementById('copyBtn');

if (navigator.clipboard && window.isSecureContext) {
navigator.clipboard.writeText(text).then(() => {
  copyBtn.textContent = 'Copied!';
  copyBtn.classList.add('copied');
  setTimeout(() => {
    copyBtn.textContent = '📋 Copy';
    copyBtn.classList.remove('copied');
  }, 1000);
}).catch(err => {
  alert(`❌ Clipboard error: ${err.message}`);
});
} else {
const textarea = document.createElement('textarea');
textarea.value = text;
textarea.style.position = 'fixed';
textarea.style.opacity = 0;
document.body.appendChild(textarea);
textarea.focus();
textarea.select();
try {
  const successful = document.execCommand('copy');
  if (successful) {
    copyBtn.textContent = 'Copied!';
    copyBtn.classList.add('copied');
    setTimeout(() => {
      copyBtn.textContent = '📋 Copy';
      copyBtn.classList.remove('copied');
    }, 1000);
  } else {
    alert('❌ Fallback copy failed');
  }
} catch (err) {
  alert(`❌ Fallback error: ${err.message}`);
}
document.body.removeChild(textarea);
}
}


function removeDuplicates() {
  const lines = textarea.value.split('\n');
  textarea.value = [...new Set(lines)].join('\n');
  updateEverything();
}

function removeEmptyLines() {
  const lines = textarea.value.split('\n');
  textarea.value = lines.filter(line => line.trim() !== '').join('\n');
  updateEverything();
}

function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');
}

updateEverything();