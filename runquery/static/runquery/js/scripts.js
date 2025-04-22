let lastExecutedResults = [];  // Store last result data

const tabButtons = document.querySelectorAll(".tab-button");
const tabContents = document.querySelectorAll(".tab-content");

// Restore vertical view preference on load
const verticalToggle = document.getElementById("toggleVertical");
const savedVertical = localStorage.getItem("verticalView") === "true";
verticalToggle.checked = savedVertical;

verticalToggle.addEventListener("change", function () {
  localStorage.setItem("verticalView", this.checked);
});

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
  });

  document.getElementById("dropdown1").addEventListener("change", function () {
    const selectedDb = this.value;
    localStorage.setItem("selectedDb", selectedDb);
    fetchTableStructure(selectedDb);
  });
  

document.getElementById("toggleSwitch").addEventListener("change", function () {
  const isColumnView = this.checked;
  document.getElementById("columnResult").style.display = isColumnView ? "block" : "none";
  document.getElementById("result").style.display = isColumnView ? "none" : "block";
});

function countChars() {
  const current = document.querySelector(".tab-content.active textarea");
  alert("Characters: " + current.value.length);
}

function execute() {
  const startTime = new Date();
  document.getElementById("queryTimer").textContent = "";

  const currentTab = document.querySelector(".tab-button.active").getAttribute("data-index");
  let queryText = document.getElementById("text-" + currentTab).value.trim();
  if (queryText.endsWith(";")) queryText = queryText.slice(0, -1);

  const dbAlias = document.getElementById("dropdown1").value;
  if (!queryText) {
    alert("Please enter a SQL query.");
    return;
  }

  const columnContainer = document.getElementById("columnResult");
  const jsonContainer = document.getElementById("jsonResult");
  columnContainer.innerHTML = '<div class="loading">Running query...</div>';
  jsonContainer.innerHTML = '<div class="loading">Running query...</div>';
  columnContainer.style.display = "block";
  jsonContainer.style.display = "none";

  fetch("/runquery/execute_oracle_queries/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ script_name: dbAlias, query_sets: [[queryText]] })
  })
    .then(res => res.json())
    .then(data => {
      const results = data.results || data;
      lastExecutedResults = results; // ✅ Save for toggle use
      document.getElementById("jsonResult").textContent = JSON.stringify(results, null, 2);
      renderResults(results);

      // Optional: save to history
      const historyEntry = {
        timestamp: new Date().toISOString(),
        database: dbAlias,
        query: queryText,
        result: results.map(r => r.result),
        error: results.map(r => r.error),
      };

      fetch("/runquery/save_history/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(historyEntry)
      });

      displayQueryTime(startTime);
    })
    .catch(err => {
      columnContainer.innerHTML = `<div style="color:red">❌ ${err.message}</div>`;
      document.getElementById("queryTimer").textContent = "❌ Query failed.";
    });
}



let tableData = {};

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

      Object.entries(data.tables).forEach(([table, columns]) => {
        renderTable(sidebar, table);
      });
    });
}

function renderTable(sidebar, table) {
  const box = document.createElement("details");
  box.className = "table-box";
  box.open = false;

  const summary = document.createElement("summary");
  summary.innerHTML = `📂 ${table} <span class="suggestion-count">(${tableData[table].length})</span>`;
  const pinIcon = document.createElement("span");
  pinIcon.className = `pin-icon`;
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
  const tables = document.querySelectorAll(".table-box");

  tables.forEach(tableDiv => {
    const tableName = tableDiv.querySelector("summary").textContent.toLowerCase();
    const columns = tableDiv.querySelectorAll("li");
    let tableMatch = tableName.includes(filter);
    let columnMatch = false;

    columns.forEach(column => {
      const columnName = column.textContent.toLowerCase();
      if (columnName.includes(filter)) {
        columnMatch = true;
      }
    });

    if (tableMatch || columnMatch) {
      tableDiv.style.display = "";
    } else {
      tableDiv.style.display = "none";
    }
  });
}

function showSuggestions() {
  const filter = document.getElementById("tableSearch").value.toLowerCase();
  const suggestionsDiv = document.getElementById("suggestions");
  suggestionsDiv.innerHTML = "";

  if (filter === "") {
    suggestionsDiv.style.display = "none";
    return;
  }

  let suggestions = [];

  for (let table in tableData) {
    if (table.toLowerCase().includes(filter)) {
      suggestions.push({ type: 'table', name: table });
    }

    tableData[table].forEach(column => {
      if (column.toLowerCase().includes(filter)) {
        suggestions.push({ type: 'column', name: `${column} (in ${table})` });
      }
    });
  }

  if (suggestions.length === 0) {
    suggestionsDiv.style.display = "none";
    return;
  }

  suggestions.forEach(suggestion => {
    const item = document.createElement("div");
    item.textContent = suggestion.name;
    item.classList.add("suggestion-item");

    if (suggestion.type === 'table') {
      const span = document.createElement("span");
      span.classList.add("suggestion-count");
      item.appendChild(span);

      item.addEventListener("click", () => {
        selectSuggestion(suggestion);
        fetchTableStructureForSuggestion(suggestion.name);
      });
    } else {
      item.addEventListener("click", () => selectSuggestion(suggestion));
    }

    suggestionsDiv.appendChild(item);
  });

  suggestionsDiv.style.display = "block";
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
  const startTime = new Date(); // ⏱ Start timer
  document.getElementById("queryTimer").textContent = ""; // Clear previous timer

  const tab = document.querySelector(".tab-button.active").getAttribute("data-index");
  const sql = document.getElementById("text-" + tab).value.trim();

  if (!sql) {
    alert("Enter a SQL query to count.");
    return;
  }

  // 👇 Wrap the user's query inside SELECT COUNT(*)
  const countWrappedQuery = `SELECT COUNT(*) AS ROW_COUNT FROM (${sql})`;

  const db = document.getElementById("dropdown1").value;

  fetch("/runquery/execute_oracle_queries/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      script_name: db,
      query_sets: [[countWrappedQuery]]
    })
  })
    .then(res => res.json())
    .then(data => {
      const result = data.results?.[0]?.result?.[0];
      if (result && result.ROW_COUNT !== undefined) {
        alert(`🧮 Count result: ${result.ROW_COUNT}`);
      } else {
        alert("Count query ran, but no rows returned.");
      }

      // ✅ Show execution time
      displayQueryTime(startTime);
    })
    .catch(err => {
      document.getElementById("queryTimer").textContent = "❌ Count query failed.";
      console.error("Count query error:", err);
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
  columnContainer.innerHTML = "";

  const isVertical = document.getElementById("toggleVertical").checked;

  results.forEach((entry, idx) => {
    const query = entry.query || "";
    const error = entry.error || "";
    const dbKey = entry.db_key || "Unknown DB";
    const queryResult = entry.result;

    const card = document.createElement("div");
    card.className = "table-box";
    card.innerHTML = `<strong>Query ${idx + 1} [${dbKey}]:</strong><br><code>${query}</code><br><br>`;

    if (error) {
      card.innerHTML += `<div style="color:red">❌ ${error}</div>`;
    } else if (Array.isArray(queryResult) && queryResult.length > 0) {
      const table = document.createElement("table");
      table.style.borderCollapse = "collapse";
      table.style.width = "100%";

      const keys = Object.keys(queryResult[0]);

      if (isVertical) {
        keys.forEach(key => {
          const tr = document.createElement("tr");
      
          const th = document.createElement("th");
          th.textContent = key;
          th.style.padding = "8px";
          th.style.background = "#f3f4f6";
          th.style.border = "1px solid #ccc";
          th.style.textAlign = "left";
          tr.appendChild(th);
      
          queryResult.forEach(row => {
            const td = document.createElement("td");
            td.textContent = row[key];
            td.style.padding = "8px";
            td.style.border = "1px solid #ccc";  // ✅ border added
            tr.appendChild(td);
          });
      
          table.appendChild(tr);
        });
      
      
      } else {
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");
        keys.forEach(k => {
          const th = document.createElement("th");
          th.textContent = k;
          th.style.padding = "8px";
          th.style.background = "#f3f4f6";
          headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement("tbody");
        queryResult.forEach(row => {
          const tr = document.createElement("tr");
          keys.forEach(k => {
            const td = document.createElement("td");
            td.textContent = row[k];
            td.style.padding = "8px";
            tr.appendChild(td);
          });
          tbody.appendChild(tr);
        });

        table.appendChild(tbody);
      }

      card.appendChild(table);
    } else {
      card.innerHTML += `<div style="color:gray">No rows returned</div>`;
    }

    columnContainer.appendChild(card);
  });
}
document.getElementById("toggleVertical").addEventListener("change", () => {
  if (lastExecutedResults && Array.isArray(lastExecutedResults)) {
    renderResults(lastExecutedResults);
  }
});
