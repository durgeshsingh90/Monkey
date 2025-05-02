let lastExecutedResults = [];  // Store last result data
let queryTimerInterval;
let sessionTimeLeft = 0;
let sessionTimerInterval = null;
let isSessionConnected = false;
let query_sets = [];
let tableData = {};
let currentPage = 1;
const rowsPerPage = 2000;
let paginatedData = [];


const tabButtons = document.querySelectorAll(".tab-button");
const tabContents = document.querySelectorAll(".tab-content");

// 🟢 Restore custom tab names (from loaded scripts)
tabButtons.forEach((btn, i) => {
  const savedName = localStorage.getItem(`tabName-${i}`);
  if (savedName) {
    btn.textContent = savedName;
  }
});

// Restore vertical view preference on load
const verticalToggle = document.getElementById("toggleVertical");
const savedVertical = localStorage.getItem("verticalView") === "true";
verticalToggle.checked = savedVertical;

verticalToggle.addEventListener("change", function () {
  localStorage.setItem("verticalView", this.checked);
});


function getCurrentEditorContent() {
  return editor.getValue();
}

function setEditorContent(text) {
  editor.setValue(text);
}

function showTab(index) {
  tabButtons.forEach(btn => btn.classList.remove("active"));
  tabContents.forEach(tab => tab.classList.remove("active"));
  tabButtons[index].classList.add("active");
  tabContents[index].classList.add("active");
  localStorage.setItem("activeTab", index);
}

tabButtons.forEach(btn => {
  btn.addEventListener("click", () => {
    const index = parseInt(btn.getAttribute("data-index"));
    showTab(index);
  });
});

const textareas = document.querySelectorAll("textarea");
textareas.forEach((textarea, idx) => {
  const saved = localStorage.getItem(`text-${idx}`);
  if (saved) textarea.value = saved;
  textarea.addEventListener("input", () => {
    localStorage.setItem(`text-${idx}`, textarea.value);
  });
});

const savedTab = localStorage.getItem("activeTab") || 0;
showTab(parseInt(savedTab));

fetch("/runquery/get_oracle_dbs/")
  .then(res => res.json())
  .then(data => {
    const dropdown = document.getElementById("dropdown1");
    dropdown.innerHTML = '';
    data.databases.forEach(db => {
      const opt = document.createElement("option");
      opt.value = db;
      opt.textContent = db;
      dropdown.appendChild(opt);
    });
    const savedDb = localStorage.getItem("selectedDb");
dropdown.value = savedDb || "uat_ist";
localStorage.setItem("selectedDb", dropdown.value);

    fetchTableStructure(dropdown.value);
    refreshScriptList(dropdown.value);
     // ✅ ADD THIS:
   updatePageTitle(dropdown.value);

  });

  document.getElementById("dropdown1").addEventListener("change", function () {
    const selectedDb = this.value;
    localStorage.setItem("selectedDb", selectedDb);
    disconnectDbSession();  // 🔌 auto-disconnect
    fetchTableStructure(selectedDb);
    refreshScriptList(selectedDb);
    updatePageTitle(selectedDb);
  });
  

document.getElementById("toggleSwitch").addEventListener("change", function () {
  const isColumnView = this.checked;
  document.getElementById("columnResult").style.display = isColumnView ? "block" : "none";
  document.getElementById("result").style.display = isColumnView ? "none" : "block";
});
const toggleEmptyCols = document.getElementById("toggleEmptyCols");
toggleEmptyCols.checked = localStorage.getItem("hideEmptyCols") === "true";
toggleEmptyCols.addEventListener("change", () => {
 localStorage.setItem("hideEmptyCols", toggleEmptyCols.checked);
 renderResults(lastExecutedResults);
});
function countChars() {
  const current = document.querySelector(".tab-content.active textarea");
  alert("Characters: " + current.value.length);
}


function execute() {
  const start = Date.now();
  const timerDiv = document.getElementById("queryTimer");
  timerDiv.textContent = "⏱ Running: 0.0s";

  clearInterval(queryTimerInterval);
  queryTimerInterval = setInterval(() => {
    const elapsed = ((Date.now() - start) / 1000).toFixed(1);
    timerDiv.textContent = `⏱ Running: ${elapsed}s`;
  }, 100);

  const currentTab = getActiveTabIndex();
  const dbAlias = document.getElementById("dropdown1").value;
  const rawText = getCurrentEditorContent(currentTab).trim();

  if (!rawText) {
    clearInterval(queryTimerInterval);
    timerDiv.textContent = "⚠️ No query provided.";
    alert("Please enter a SQL query.");
    return;
  }

  const columnContainer = document.getElementById("columnResult");
  const jsonContainer = document.getElementById("jsonResult");
  columnContainer.innerHTML = '<div class="loading">Running query...</div>';
  jsonContainer.innerHTML = '';
  columnContainer.style.display = "block";
  jsonContainer.style.display = "none";

  // Always attempt new connection with fresh 10-min session
  updateDbSessionIcon("connecting");

  fetch("/runquery/start_db_session/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ db_key: dbAlias, force_new: true })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        sessionTimeLeft = 600;
        isSessionConnected = true;
        updateDbSessionIcon("connected");
        startSessionCountdown();

        // Proceed with query execution after connection established
        runQueryAfterConnect(dbAlias, rawText, start, timerDiv);
      } else {
        updateDbSessionIcon("disconnected");
        clearInterval(queryTimerInterval);
        timerDiv.textContent = "❌ Connection failed.";
        alert("❌ " + data.error);
      }
    })
    .catch(() => {
      updateDbSessionIcon("disconnected");
      clearInterval(queryTimerInterval);
      timerDiv.textContent = "❌ Connection failed.";
      alert("❌ Failed to connect to database.");
    });
}
function runQueryAfterConnect(dbAlias, rawText, start, timerDiv) {
  const rawLines = rawText.split(/\r?\n/).map(l => l.trim());
  const nonCommentedLines = rawLines.filter(line => !line.startsWith("--") && line !== "");
  const cleanText = nonCommentedLines.join("\n");

  const querySets = extractQuerySetsFromText(cleanText);
  let query_sets = [];

  if (Object.keys(querySets).length > 0) {
    query_sets = Object.values(querySets);  // Parallel sets
  } else {
    const selectQueries = cleanText
      .split(";")
      .map(q => q.trim())
      .filter(q => q.toLowerCase().startsWith("select") && q.length > 0);
    query_sets = [selectQueries];  // Sequential
  }

  fetch("/runquery/execute_oracle_queries/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      script_name: dbAlias,
      query_sets: query_sets,
      use_session: sessionTimeLeft > 0
    })
  })
    .then(res => res.json())
    .then(data => {
      clearInterval(queryTimerInterval);
      const totalSeconds = ((Date.now() - start) / 1000).toFixed(2);
      timerDiv.textContent = `✔ Completed in ${totalSeconds}s`;

      const results = data.results || data;
      lastExecutedResults = results;
      renderResults(results);

      // ✅ Send to detached window if open
      if (resultWindow && !resultWindow.closed && results[0]?.result) {
        resultWindow.postMessage(results[0].result, "*");
      }

      const historyEntry = {
        timestamp: new Date().toISOString(),
        database: dbAlias,
        query: rawText,
        result: results.map(r => r.result),
        error: results.map(r => r.error),
        duration: totalSeconds
      };

      fetch("/runquery/save_history/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(historyEntry)
      });
    })
    .catch(err => {
      clearInterval(queryTimerInterval);
      const rawMsg = err.message || "Query execution failed";
      const match = rawMsg.match(/ORA-\d{5}:.*$/);
      const cleanError = match ? match[0] : rawMsg;

      const columnContainer = document.getElementById("columnResult");
      columnContainer.innerHTML = `
        <div style="
          color: #b91c1c;
          background: #fee2e2;
          padding: 14px 18px;
          border-radius: 12px;
          font-weight: 600;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
          margin: 12px 0;
          font-size: 15px;
        ">
          ❌ ${cleanError}
        </div>
      `;
      timerDiv.textContent = "❌ Query failed.";
    });
}

function extractQuerySetsFromText(text) {
  const sets = {};
  const lines = text.split("\n");

  let currentSet = null;
  for (let line of lines) {
    line = line.trim();
    if (/^query_set_\d+\s*=\s*\[?/i.test(line)) {
      currentSet = line.split("=")[0].trim();
      sets[currentSet] = [];
    } else if (currentSet && line && !line.startsWith("//")) {
      const query = line.replace(/^["'\[]+|["'\],;]+$/g, "").trim();
      if (query) sets[currentSet].push(query);
    }
  }

  return sets;
}






function fetchTableStructure(dbKey, refresh = false) {
  const url = `/runquery/get_table_structure/?db=${dbKey}${refresh ? '&refresh=1' : ''}`;
  const sidebar = document.getElementById("tableStructure");

  if (refresh) {
    sidebar.innerHTML = `<div style="color: gray;">⏳ Fetching from DB...</div>`;
  }

  fetch(url)
    .then(res => res.json())
    .then(data => {
      tableData = data.tables;
      sidebar.innerHTML = '';

      const tableCountEl = document.querySelector('#sidebar h3');
      tableCountEl.textContent = `📘 Tables (${data.count})`;

      if (data.error) {
        sidebar.innerHTML = `<div style="color:red">${data.error}</div>`;
        return;
      }

      const pinnedTables = JSON.parse(localStorage.getItem("pinnedTables") || "[]");

const sortedTables = Object.keys(data.tables).sort((a, b) => {
  const aPinned = pinnedTables.includes(a);
  const bPinned = pinnedTables.includes(b);
  if (aPinned && !bPinned) return -1;
  if (!aPinned && bPinned) return 1;
  return a.localeCompare(b); // fallback to alphabetical
});

sortedTables.forEach(table => {
  renderTable(sidebar, table);
});

    });
}
function registerSchemaAutocomplete(tableData) {
  monaco.languages.registerCompletionItemProvider('sql', {
    triggerCharacters: [' ', '.', ','],
    provideCompletionItems: function (model, position) {
      const fullText = model.getValue();
      const match = fullText.match(/from\s+([\w]+)\.([\w]+)/i);

      if (!match) return { suggestions: [] };

      const schema = match[1].toUpperCase();
      const table = match[2].toUpperCase();
      const fullKey = `${schema}.${table}`;
      const columns = tableData[fullKey] || [];

      const suggestions = columns.map(col => ({
        label: col,
        kind: monaco.languages.CompletionItemKind.Field,
        insertText: col,
        documentation: `Column from ${fullKey}`
      }));

      return { suggestions };
    }
  });
}
async function fetchAndRegisterColumns(dbKey, tableFullName) {
  const response = await fetch("/runquery/get_metadata_columns/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ db_key: dbKey, query: `FROM ${tableFullName}` })
  });
  const data = await response.json();
  if (!data.columns) return [];

  tableData[tableFullName.toUpperCase()] = data.columns;  // Cache it
  return data.columns;
}


function renderTable(sidebar, table) {
  const box = document.createElement("details");
  box.className = "table-box";
  box.open = false;

  const summary = document.createElement("summary");
  summary.innerHTML = `<span class="arrow-icon">▶</span> ${table} <span class="suggestion-count">(${tableData[table].length})</span>`;
  box.addEventListener("toggle", () => {
    const arrow = box.querySelector(".arrow-icon");
    if (box.open) {
      arrow.textContent = "▼";
    } else {
      arrow.textContent = "▶";
    }
  });
  
  const pinIcon = document.createElement("span");
  const pinnedTables = JSON.parse(localStorage.getItem("pinnedTables") || "[]");
  const isPinned = pinnedTables.includes(table);
  pinIcon.className = "pin-icon" + (isPinned ? " pinned" : "");
  pinIcon.textContent = isPinned ? "📍" : "📌";

  pinIcon.addEventListener("click", (e) => togglePin(table, e));
  summary.appendChild(pinIcon);

  box.appendChild(summary);

  const ul = document.createElement("ul");
  tableData[table].forEach(col => {
    const li = document.createElement("li");
    li.textContent = col;
    ul.appendChild(li);
  });
  box.appendChild(ul);

  sidebar.appendChild(box);
}


function togglePin(table, event) {
  event.stopPropagation();
  const pinIcon = event.target;
  const pinnedTables = JSON.parse(localStorage.getItem("pinnedTables") || "[]");

  const isPinned = pinnedTables.includes(table);
  const updatedPins = isPinned
    ? pinnedTables.filter(t => t !== table)
    : [...pinnedTables, table];

  localStorage.setItem("pinnedTables", JSON.stringify(updatedPins));
  fetchTableStructure(document.getElementById("dropdown1").value);
}


function refreshMetadata() {
  const dbKey = document.getElementById("dropdown1").value;
  fetchTableStructure(dbKey, true);
}

function filterTables() {
  const filter = document.getElementById("tableSearch").value.toLowerCase();
  const pinnedOnly = document.getElementById("pinnedOnlyToggle").checked;
  const tables = document.querySelectorAll(".table-box");

  tables.forEach(tableDiv => {
    const summary = tableDiv.querySelector("summary");
    const tableName = summary.textContent.toLowerCase();
    const isPinned = tableDiv.querySelector(".pin-icon")?.classList.contains("pinned");
    const allColumns = tableDiv.querySelectorAll("li");

    let tableMatches = tableName.includes(filter);
    let columnMatchFound = false;

    allColumns.forEach(column => {
      const colName = column.textContent.toLowerCase();

      if (tableMatches) {
        column.style.display = ""; // show all if table name matched
      } else if (colName.includes(filter)) {
        column.style.display = ""; // show only matched columns
        columnMatchFound = true;
      } else {
        column.style.display = "none"; // hide unmatched columns
      }
    });

    const shouldShow = (!pinnedOnly || isPinned) && (tableMatches || columnMatchFound);
    tableDiv.style.display = shouldShow ? "" : "none";

    // Optional: auto-expand if something matched
    tableDiv.open = shouldShow;
  });
}


function selectSuggestion(suggestion) {
  const searchInput = document.getElementById("tableSearch");
  const name = suggestion.type === 'column' ? suggestion.name.split(' ')[0] : suggestion.name;
  searchInput.value = name; // Only use table or column name
  document.getElementById("suggestions").style.display = "none";
  filterTables(); // Call the filter function after selection
}

function fetchTableStructureForSuggestion(tableName) {
  const dbKey = document.getElementById("dropdown1").value;
  const detailElement = document.querySelector(`details[summary*="${tableName}"]`);
  if (detailElement && !detailElement.open) {
    detailElement.open = true;
  }
}
function toggleViewMode(toggle) {
  const isColumn = toggle.checked;

  document.getElementById("columnResult").style.display = isColumn ? "block" : "none";
  document.getElementById("jsonResult").style.display = isColumn ? "none" : "block";

  const icon = document.getElementById("toggleIcon");
  icon.src = isColumn
    ? "/static/runquery/images/tablet.png"
    : "/static/runquery/images/json.png";

  localStorage.setItem("viewMode", isColumn ? "column" : "json");
}



// Restore saved view mode preference This line must be after toggle View mode
const savedView = localStorage.getItem("viewMode") || "column";
const toggle = document.getElementById("toggleSwitch");
toggle.checked = savedView === "column";
toggleViewMode(toggle);  // will update icon too

function countQuery() {
  const start = Date.now();
  const timerDiv = document.getElementById("queryTimer");
  timerDiv.textContent = "⏱ Counting...";

  const currentTab = getActiveTabIndex();
  const dbAlias = document.getElementById("dropdown1").value;
  const rawText = getCurrentEditorContent(currentTab).trim();

  if (!rawText) {
    timerDiv.textContent = "⚠️ No query provided.";
    alert("Please enter a SQL query.");
    return;
  }

  // Auto-connect if not already connected
  if (!isSessionConnected) {
    fetch("/runquery/start_db_session/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ db_key: dbAlias })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          sessionTimeLeft = data.remaining;
          isSessionConnected = true;
          updateDbSessionIcon();
          startSessionCountdown();
        }
      });
  } else {
    sessionTimeLeft = 600;
    startSessionCountdown();
  }

  const lines = rawText
    .split(";")
    .map(line => line.trim())
    .filter(line => line && !line.startsWith("--"));

  const wrappedQueries = lines.map(q => `SELECT COUNT(*) FROM (${q})`);

  fetch("/runquery/execute_oracle_queries/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      script_name: dbAlias,
      query_sets: [wrappedQueries],
      use_session: sessionTimeLeft > 0
    })
  })
    .then(res => res.json())
    .then(data => {
      const totalSeconds = ((Date.now() - start) / 1000).toFixed(2);
      timerDiv.textContent = `✔ Count completed in ${totalSeconds}s`;

      const results = data.results || data;
      lastExecutedResults = results;
      renderResults(results);
    })
    .catch(err => {
      const rawMsg = err.message || "Query execution failed";
      const match = rawMsg.match(/ORA-\d{5}:.*$/);
      const cleanError = match ? match[0] : rawMsg;

      const columnContainer = document.getElementById("columnResult");
      columnContainer.innerHTML = `
        <div style="
          color: #b91c1c;
          background: #fee2e2;
          padding: 14px 18px;
          border-radius: 12px;
          font-weight: 600;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
          margin: 12px 0;
          font-size: 15px;
        ">
          ❌ ${cleanError}
        </div>
      `;
      timerDiv.textContent = "❌ Count failed.";
    });
}


function displayQueryTime(startTime) {
  const endTime = new Date();
  const diffSec = (endTime - startTime) / 1000;

  const timerDiv = document.getElementById("queryTimer");
  if (diffSec > 5) {
    timerDiv.textContent = `⏱ Query ran in ${diffSec.toFixed(2)} seconds`;
  } else {
    timerDiv.textContent = "";
  }
}

function scrollRight() {
  const wrapper = document.querySelector(".scroll-wrapper");
  if (wrapper) {
    wrapper.scrollBy({ left: 300, behavior: "smooth" });
  }
}

function updateScrollButtonVisibility() {
  const wrapper = document.querySelector(".scroll-wrapper");
  const btn = document.getElementById("scrollRightBtn");
  if (wrapper && wrapper.scrollWidth > wrapper.clientWidth + 10) {
    btn.style.display = "block";
  } else {
    btn.style.display = "none";
  }
}
function renderResults(results) {
  const columnContainer = document.getElementById("columnResult");
  const jsonContainer = document.getElementById("jsonResult");
  const exportContainer = document.getElementById("exportDropdownContainer");
  const copyBtn = document.getElementById("copyJsonBtn");
  const isVertical = document.getElementById("toggleVertical").checked;
  const hideEmptyCols = document.getElementById("toggleEmptyCols")?.checked;

  columnContainer.innerHTML = "";
  jsonContainer.innerHTML = "";
  document.getElementById("paginationControls")?.remove();

  if (!results || results.length === 0 || !results[0].result || results[0].result.length === 0) {
    exportContainer.style.display = "none";
    copyBtn.style.display = "none";
    columnContainer.innerHTML = "<div>No rows returned.</div>";
    return;
  }

  exportContainer.style.display = "inline-block";
  copyBtn.style.display = "inline-block";

  // Set paginatedData globally and reset to page 1
  paginatedData = results[0].result;
  currentPage = 1;

  // Filter empty columns if needed
  if (hideEmptyCols && paginatedData.length > 0) {
    const keys = Object.keys(paginatedData[0]);
    const nonEmptyKeys = keys.filter(k =>
      paginatedData.some(row => row[k] !== null && row[k] !== undefined && row[k] !== "")
    );
    paginatedData = paginatedData.map(row => {
      const filtered = {};
      nonEmptyKeys.forEach(k => filtered[k] = row[k]);
      return filtered;
    });
  }

  renderPage(currentPage);
}

document.getElementById("toggleVertical").addEventListener("change", () => {
  if (lastExecutedResults && Array.isArray(lastExecutedResults)) {
    renderResults(lastExecutedResults);
  }
});

function renderPage(pageNumber) {
  const columnContainer = document.getElementById("columnResult");
  const jsonContainer = document.getElementById("jsonResult");
  columnContainer.innerHTML = "";
  jsonContainer.innerHTML = "";

  const isVertical = document.getElementById("toggleVertical").checked;

  const start = (pageNumber - 1) * rowsPerPage;
  const end = start + rowsPerPage;
  const pageRows = paginatedData.slice(start, end);

  if (!pageRows || pageRows.length === 0) {
    columnContainer.innerHTML = "<div>No rows to display.</div>";
    return;
  }

  const keys = Object.keys(pageRows[0]);

  const card = document.createElement("div");
  card.className = "table-box";

  const table = document.createElement("table");
  table.style.borderCollapse = "collapse";
  table.style.width = "max-content";
  const scrollWrapper = document.createElement("div");
  scrollWrapper.style.overflowX = "auto";
  scrollWrapper.style.width = "100%";
  scrollWrapper.appendChild(table);

  if (isVertical) {
    // Vertical orientation
    keys.forEach(key => {
      const tr = document.createElement("tr");

      const th = document.createElement("th");
      th.textContent = key;
      th.style.padding = "8px";
      th.style.background = "#f3f4f6";
      th.style.border = "1px solid #ccc";
      th.style.textAlign = "left";
      tr.appendChild(th);

      pageRows.forEach(row => {
        const td = document.createElement("td");
        td.textContent = row[key];
        td.style.padding = "8px";
        td.style.border = "1px solid #ccc";
        tr.appendChild(td);
      });

      table.appendChild(tr);
    });
  } else {
    // Horizontal orientation (row-wise)
    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    // Row number header
    const rowNumTh = document.createElement("th");
    rowNumTh.textContent = "#";
    rowNumTh.style.padding = "8px";
    rowNumTh.style.background = "#f3f4f6";
    rowNumTh.style.border = "1px solid #ccc";
    headerRow.appendChild(rowNumTh);

    keys.forEach(k => {
      const th = document.createElement("th");
      th.textContent = k;
      th.style.padding = "8px";
      th.style.background = "#f3f4f6";
      th.style.border = "1px solid #ccc";
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    pageRows.forEach((row, idx) => {
      const tr = document.createElement("tr");

      // Row number cell
      const rowNumTd = document.createElement("td");
      rowNumTd.textContent = start + idx + 1;
      rowNumTd.style.padding = "6px";
      rowNumTd.style.border = "1px solid #ccc";
      rowNumTd.style.background = "#f9fafb";
      tr.appendChild(rowNumTd);

      keys.forEach(k => {
        const td = document.createElement("td");
        td.textContent = row[k];
        td.style.padding = "6px";
        td.style.border = "1px solid #ccc";
        tr.appendChild(td);
      });

      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
  }

  card.appendChild(scrollWrapper);
  columnContainer.appendChild(card);

  // JSON view
  const jsonCard = document.createElement("pre");
  jsonCard.style.padding = "1rem";
  jsonCard.style.borderRadius = "8px";
  jsonCard.style.background = "#fafafa";
  jsonCard.style.border = "1px solid #eee";
  jsonCard.style.marginTop = "1rem";
  jsonCard.textContent = JSON.stringify(pageRows, null, 2);
  jsonContainer.appendChild(jsonCard);

  // Show/hide based on toggle
  const isColumnView = document.getElementById("toggleSwitch").checked;
  columnContainer.style.display = isColumnView ? "block" : "none";
  jsonContainer.style.display = isColumnView ? "none" : "block";

  // Render pagination controls
  renderPaginationControls(pageNumber);

  // Optional: sticky scroll sync
  syncStickyScrollBar();
}

function renderPaginationControls(current) {
  const totalPages = Math.ceil(paginatedData.length / rowsPerPage);
  const container = document.getElementById("paginationControls") || document.createElement("div");

  container.id = "paginationControls";
  container.style.marginTop = "10px";
  container.style.textAlign = "center";

  container.innerHTML = "";

  const prevBtn = document.createElement("button");
  prevBtn.textContent = "⬅️ Previous";
  prevBtn.disabled = current <= 1;
  prevBtn.onclick = () => {
    currentPage -= 1;
    renderPage(currentPage);
  };
  container.appendChild(prevBtn);

  const info = document.createElement("span");
  info.style.margin = "0 10px";
  info.textContent = `Page ${current} of ${totalPages}`;
  container.appendChild(info);

  const nextBtn = document.createElement("button");
  nextBtn.textContent = "Next ➡️";
  nextBtn.disabled = current >= totalPages;
  nextBtn.onclick = () => {
    currentPage += 1;
    renderPage(currentPage);
  };
  container.appendChild(nextBtn);

  document.getElementById("columnResult").appendChild(container);
}


function saveCurrentScript() {
  const name = document.getElementById("scriptName").value.trim();
  const tabIndex = getActiveTabIndex();
  let queryText = getCurrentEditorContent(tabIndex).trim();
  const db = document.getElementById("dropdown1").value;  // get selected DB
  if (!name || !queryText) {
    alert("Missing info to save script!");
    return;
  }
  const saveBtn = document.getElementById("saveBtn");
  fetch("/runquery/save_script/", {
    method: "POST",
    body: JSON.stringify({ name, query: queryText, created_from: db }),
    headers: { "Content-Type": "application/json" },
  }).then(res => res.json())
    .then(data => {
      if (data.success) {
        saveBtn.textContent = "✅ Saved";
        saveBtn.style.backgroundColor = "#22c55e";
        setTimeout(() => {
          saveBtn.textContent = "💾 Save";
          saveBtn.style.backgroundColor = "";
        }, 1000);
        refreshScriptList();
      }
    });
 }
 



function toggleScriptDropdown() {
  const list = document.getElementById("scriptList");
  list.style.display = list.style.display === "none" ? "block" : "none";
}

function refreshScriptList() {
  const container = document.getElementById("scriptList");
  container.innerHTML = "";
  fetch(`/runquery/list_scripts/`)
    .then(res => res.json())
    .then(data => {
      (data.scripts || []).forEach(script => {
        const row = document.createElement("div");
        row.className = "script-item";
        row.style.display = "flex";
        row.style.justifyContent = "space-between";
        row.style.alignItems = "center";
        row.style.padding = "6px 10px";
        row.style.cursor = "pointer";
        row.style.borderBottom = "1px solid #eee";
        const nameSpan = document.createElement("span");
        nameSpan.innerHTML = `${script.name} <small style="color: gray;">(${script.created_from || 'unknown'})</small>`;
        nameSpan.style.flex = "1";
        const deleteSpan = document.createElement("span");
        deleteSpan.textContent = "✖";
        deleteSpan.className = "delete-icon";
        deleteSpan.style.color = "red";
        deleteSpan.style.marginLeft = "10px";
        deleteSpan.addEventListener("click", (e) => {
          e.stopPropagation();
          deleteScriptByName(script.name);
        });
        row.addEventListener("click", () => {
          loadScriptByName(script.name);
          document.getElementById("scriptName").value = script.name;
          toggleScriptDropdown();
        });
        row.appendChild(nameSpan);
        row.appendChild(deleteSpan);
        container.appendChild(row);
      });
      if ((data.scripts || []).length === 0) {
        const empty = document.createElement("div");
        empty.textContent = "No saved scripts.";
        empty.style.padding = "10px";
        empty.style.color = "gray";
        container.appendChild(empty);
      }
    })
    .catch(err => {
      const error = document.createElement("div");
      error.textContent = `❌ Error loading scripts: ${err.message}`;
      error.style.color = "red";
      error.style.padding = "10px";
      container.appendChild(error);
    });
 }
 function loadScriptByName(name) {
  const tabIndex = getActiveTabIndex();
  fetch(`/runquery/load_script/?name=${name}`)
    .then(res => res.json())
    .then(data => {
      if (data.query !== undefined) {
        setEditorContent(tabIndex, data.query);
        document.getElementById("scriptName").value = name;
      } else {
        alert("⚠️ No content found in saved script.");
      }
    })
    .catch(err => {
      alert("❌ Failed to load script: " + err.message);
    });
 }



 function deleteScriptByName(name) {
  fetch("/runquery/delete_script/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  }).then(res => res.json())
    .then(data => {
      if (data.success) {
        refreshScriptList();
      }
    });
 }




function clearSearch() {
  const search = document.getElementById("tableSearch");
  search.value = "";
  filterTables();
  document.getElementById("clearBtn").style.display = "none";
}

// Show/hide ✖ button dynamically
document.getElementById("tableSearch").addEventListener("input", function () {
  const clearBtn = document.getElementById("clearBtn");
  clearBtn.style.display = this.value.length > 0 ? "block" : "none";
});

// const db = this.value;
// refreshScriptList(db);

const editors = {};  // to store editor instances

require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs' }});

require(['vs/editor/editor.main'], function () {
  for (let i = 0; i < 9; i++) {
    editors[`editor-${i}`] = monaco.editor.create(document.getElementById(`editor-${i}`), {
      value: `-- SQL for Tab ${i + 1}`,
      language: "sql",
      theme: "vs-dark",
      automaticLayout: true,
      minimap: { enabled: false }
    });
    setupAutoSave(i);
    loadTabContent(i);
  }
// monaco.editor.defineTheme('fef8e6-theme', {
//   base: 'vs-dark', // or 'vs' for light base
//   inherit: true,
//   rules: [],
//   colors: {
//     'editor.background': '#222222',
//     'editor.foreground': '#000000',
//     'editorLineNumber.foreground': '#888',
//     'editorLineNumber.activeForeground': '#222',
//     'editorCursor.foreground': '#333',
//     'editorIndentGuide.background': '#e0dccc',
//     'editorIndentGuide.activeBackground': '#d4cdb9'
//   }
// });

// monaco.editor.setTheme('fef8e6-theme');

  // ✅ Now Monaco is guaranteed to be ready
  if (Object.keys(tableData).length > 0) {
    registerSchemaAutocomplete(tableData);
  }
});

function setupAutoSave(tabIndex) {
  const editor = editors[`editor-${tabIndex}`];
  if (!editor) return;

  let timeout;
  editor.onDidChangeModelContent(() => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      const content = editor.getValue();
      fetch("/runquery/save_tab_content/", {
        method: "POST",
        body: JSON.stringify({ tab: tabIndex, content }),
        headers: { "Content-Type": "application/json" },
      });
    }, 1000); // save 1 second after user stops typing
  });
}

function loadTabContent(tabIndex) {
  fetch(`/runquery/load_tab_content/?tab=${tabIndex}`)
    .then(res => res.json())
    .then(data => {
      if (data.success && data.content !== undefined) {
        editors[`editor-${tabIndex}`].setValue(data.content);
      }
    });
}

function getCurrentEditorContent(tabIndex) {
  const editor = editors[`editor-${tabIndex}`];
  return editor ? editor.getValue() : "";
}

function setEditorContent(tabIndex, content) {
  const editor = editors[`editor-${tabIndex}`];
  if (editor) editor.setValue(content);
}

function getActiveTabIndex() {
  for (let i = 0; i < 9; i++) {
    if (document.getElementById(`tab-${i}`).classList.contains("active")) {
      return i;
    }
  }
  return 0;
}


document.addEventListener("keydown", function (e) {
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const ctrl = isMac ? e.metaKey : e.ctrlKey;

  // Ctrl+S = Save
  if (ctrl && e.key.toLowerCase() === 's') {
    e.preventDefault();
    saveCurrentScript();
  }

  // Shift+Enter = Execute
  if (e.shiftKey && e.key === "Enter") {
    e.preventDefault();
    execute();
  }

  // Alt+1 to Alt+9 = Switch Tabs
  if (e.altKey && /^[1-9]$/.test(e.key)) {
    e.preventDefault();
    const index = parseInt(e.key, 10) - 1;
    showTab(index);
  }
});


function collapseAllTables() {
  const detailsList = document.querySelectorAll("#tableStructure details");
  detailsList.forEach(details => {
    details.open = false;
    const arrow = details.querySelector(".arrow-icon");
    if (arrow) arrow.textContent = "▶";
  });
}
function toggleExportDropdown() {
  const exportDiv = document.getElementById("exportOptions");
  exportDiv.style.display = exportDiv.style.display === "none" ? "block" : "none";
 }
 function exportResult(type) {
  if (!lastExecutedResults || lastExecutedResults.length === 0) {
    alert("No result to export.");
    return;
  }
  const hideEmptyCols = document.getElementById("toggleEmptyCols")?.checked;
  const resultData = lastExecutedResults[0]?.result || [];
  let keys = Object.keys(resultData[0] || {});
  if (hideEmptyCols) {
    keys = keys.filter(key =>
      resultData.some(row => row[key] !== null && row[key] !== undefined && row[key] !== "")
    );
  }
  const filteredData = resultData.map(row => {
    const filteredRow = {};
    keys.forEach(k => filteredRow[k] = row[k]);
    return filteredRow;
  });
  if (type === 'json') {
    const blob = new Blob([JSON.stringify(filteredData, null, 2)], { type: "application/json" });
    downloadBlob(blob, "export.json");
  }
  else if (type === 'sql') {
    let sqlInserts = "";
    if (filteredData.length > 0) {
      const tableName = "export_table";
      const columns = keys;
      filteredData.forEach(row => {
        const values = columns.map(col => row[col] !== null ? `'${row[col]}'` : 'NULL').join(", ");
        sqlInserts += `INSERT INTO ${tableName} (${columns.join(", ")}) VALUES (${values});\n`;
      });
    }
    const blob = new Blob([sqlInserts], { type: "text/sql" });
    downloadBlob(blob, "export.sql");
  }
  else if (type === 'excel') {
    exportToExcel(filteredData);
  }
 }
 function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = "none";
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
 }
 function exportToExcel(data) {
  const worksheet = XLSX.utils.json_to_sheet(data);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Sheet1");
  XLSX.writeFile(workbook, "export.xlsx");
 }
 function syncStickyScrollBar() {
  const tableWrapper = document.querySelector("#columnResult .table-box div"); // the scrollable <div> inside .table-box
  const stickyScrollBar = document.getElementById("stickyScrollBar");
  const stickyScrollInner = document.getElementById("stickyScrollInner");
  if (!tableWrapper || tableWrapper.scrollWidth <= tableWrapper.clientWidth) {
    stickyScrollBar.style.display = "none";
    return;
  }
  stickyScrollBar.style.display = "block";
  stickyScrollBar.style.width = tableWrapper.clientWidth + "px";
  stickyScrollBar.style.left = tableWrapper.getBoundingClientRect().left + "px";
  stickyScrollInner.style.width = tableWrapper.scrollWidth + "px";
  // Sync both scrolls
  stickyScrollBar.onscroll = () => {
    tableWrapper.scrollLeft = stickyScrollBar.scrollLeft;
  };
  tableWrapper.onscroll = () => {
    stickyScrollBar.scrollLeft = tableWrapper.scrollLeft;
  };
 }

 const dbColors = {
  "prod_main": "#dc2626",  
  "uat_ist": "#facc15",    
  "sit_env": "#60a5fa",    
  "dev_db": "#4ade80",      
  "default": "#ffb347"      
 };
 function updatePageTitle(dbName) {
  const titleEl = document.getElementById("pageTitle");
  const themeColorEl = document.getElementById("themeColorMeta");
  if (titleEl) {
    titleEl.textContent = `🛢️ ${dbName} | Query Runner`;
  }
  if (themeColorEl) {
    const dbKey = dbName.toLowerCase();
    const color = dbColors[dbKey] || dbColors["default"];
    themeColorEl.setAttribute("content", color);
  }
 }
 
 function cleanEditorLines() {
  const index = getActiveTabIndex();
  const editor = editors[`editor-${index}`];
  if (!editor) return;

  const content = editor.getValue();
  const cleaned = content
    .split("\n")
    .filter(line => line.trim() !== "")
    .join("\n");

  editor.setValue(cleaned);
}


function playCleanAnimation() {
  const icon = document.getElementById("cleanIcon");

  const pngSrc = icon.getAttribute("data-png");
  const gifSrc = icon.getAttribute("data-gif");

  // Switch to GIF
  icon.src = gifSrc + "?t=" + new Date().getTime(); // prevent caching

  // Run cleaning logic
  cleanEditorLines();

  // After animation ends, switch back to PNG
  setTimeout(() => {
    icon.src = pngSrc;
  }, 1200); // Adjust based on your GIF duration
}



function startDbSession() {
  const dbKey = document.getElementById("dropdown1").value;
  updateDbSessionIcon("connecting"); // Show connecting.gif

  fetch("/runquery/start_db_session/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ db_key: dbKey, force_new: true }) // <-- force flag
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        sessionTimeLeft = 600;  // Always fresh timer
        isSessionConnected = true;
        updateDbSessionIcon("connected");
        startSessionCountdown();
      } else {
        updateDbSessionIcon("disconnected");
        alert("❌ " + data.error);
      }
    })
    .catch(() => {
      updateDbSessionIcon("disconnected");
      alert("❌ Failed to connect to database.");
    });
}

function startSessionCountdown() {
  clearInterval(sessionTimerInterval);
  updateSessionTimerText();

  sessionTimerInterval = setInterval(() => {
    sessionTimeLeft -= 1;
    updateSessionTimerText();
    if (sessionTimeLeft <= 0) {
      clearInterval(sessionTimerInterval);
      document.getElementById("sessionTimer").textContent = "⏱ Expired";
    }
  }, 1000);
}


function toggleDbSession() {
  if (isSessionConnected) {
    disconnectDbSession(true);
  } else {
    startDbSession();
  }
}

function disconnectDbSession(showMessage = false) {
  clearInterval(sessionTimerInterval);
  sessionTimeLeft = 0;
  isSessionConnected = false;
  updateDbSessionIcon();
  document.getElementById("sessionTimer").textContent = "";
  if (showMessage) alert("🔌 Disconnected from DB session.");
}

function updateSessionTimerText() {
  const mins = Math.floor(sessionTimeLeft / 60);
  const secs = sessionTimeLeft % 60;
  document.getElementById("sessionTimer").textContent = `⏱ ${mins}:${secs.toString().padStart(2, '0')}`;
}

function updateDbSessionIcon(state = "disconnected") {
  const icon = document.getElementById("dbSessionIcon");
  const srcMap = {
    connected: "/static/runquery/images/connected.png",
    disconnected: "/static/runquery/images/unplugged.png",
    connecting: "/static/runquery/images/connecting.gif"
  };
  icon.src = srcMap[state];
}

window.addEventListener("beforeunload", () => {
  disconnectDbSession();  // ⛔ auto disconnect on page refresh
});

editor.onDidChangeModelContent(debounce(async () => {
  const dbKey = document.getElementById("dropdown1").value;
  const query = editor.getValue();

  const fromMatch = query.match(/from\s+([\w.]+)/i);
  if (!fromMatch) return;

  const tableName = fromMatch[1].split('.').pop();

  const response = await fetch("/runquery/get_metadata_columns/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ db_key: dbKey, query })
  });

  const data = await response.json();
  if (!data.columns) return;

  monaco.languages.registerCompletionItemProvider("sql", {
    provideCompletionItems: () => {
      const suggestions = data.columns.map(col => ({
        label: col,
        kind: monaco.languages.CompletionItemKind.Field,
        insertText: col
      }));
      return { suggestions };
    }
  });
}, 800));

function debounce(func, wait) {
  let timeout;
  return function () {
    const context = this,
      args = arguments;
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(context, args), wait);
  };
}


function copyJsonResult() {
  const btn = document.getElementById("copyJsonBtn");

  const resultData = lastExecutedResults[0]?.result || [];
  if (!resultData || resultData.length === 0) {
    alert("No result to copy.");
    return;
  }

  const jsonText = JSON.stringify(resultData, null, 2);
  navigator.clipboard.writeText(jsonText).then(() => {
    btn.textContent = "✔ Copied JSON";
    btn.disabled = true;
    setTimeout(() => {
      btn.textContent = "📋 Copy";
      btn.disabled = false;
    }, 2000);
  }).catch(err => {
    alert("❌ Failed to copy JSON: " + err);
  });
}

let resultWindow = null;

function detachResultWindow() {
  if (resultWindow && !resultWindow.closed) {
    resultWindow.focus();
    return;
  }

  resultWindow = window.open("", "DetachedResultWindow", "width=1200,height=800");
  resultWindow.document.write(`
    <html>
    <head>
      <title>Detached Result</title>
      <style>
        body { font-family: sans-serif; margin: 0; padding: 1rem; }
        pre { white-space: pre-wrap; background: #f8f8f8; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { padding: 8px; border: 1px solid #ccc; }
        thead { background: #f3f4f6; }
      </style>
    </head>
    <body>
      <h2>🔎 Result</h2>
      <div id="detachedResultContainer">Waiting for data...</div>
      <script>
        window.addEventListener('message', function(e) {
          const data = e.data;
          if (!data || !Array.isArray(data)) return;

          const container = document.getElementById("detachedResultContainer");
          container.innerHTML = '';

          if (data.length === 0) {
            container.innerHTML = "<div>No rows returned.</div>";
            return;
          }

          const keys = Object.keys(data[0]);
          const table = document.createElement("table");

          const thead = document.createElement("thead");
          const trHead = document.createElement("tr");
          const rowNumTh = document.createElement("th");
          rowNumTh.textContent = "#";
          trHead.appendChild(rowNumTh);
          keys.forEach(k => {
            const th = document.createElement("th");
            th.textContent = k;
            trHead.appendChild(th);
          });
          thead.appendChild(trHead);
          table.appendChild(thead);

          const tbody = document.createElement("tbody");
          data.forEach((row, idx) => {
            const tr = document.createElement("tr");
            const rowNum = document.createElement("td");
            rowNum.textContent = idx + 1;
            tr.appendChild(rowNum);

            keys.forEach(k => {
              const td = document.createElement("td");
              td.textContent = row[k];
              tr.appendChild(td);
            });

            tbody.appendChild(tr);
          });

          table.appendChild(tbody);
          container.appendChild(table);
        });
      </script>
    </body>
    </html>
  `);

  // Wait for the new window to fully load before sending data
  setTimeout(() => {
    if (resultWindow && lastExecutedResults[0]?.result) {
      resultWindow.postMessage(lastExecutedResults[0].result, "*");
    }
  }, 500);
}
