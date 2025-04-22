const tabButtons = document.querySelectorAll(".tab-button");
const tabContents = document.querySelectorAll(".tab-content");

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
    dropdown.value = "uat_ist";
    fetchTableStructure(dropdown.value);
  });

document.getElementById("dropdown1").addEventListener("change", function () {
  fetchTableStructure(this.value);
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
  const currentTab = document.querySelector(".tab-button.active").getAttribute("data-index");
  const queryText = document.getElementById("text-" + currentTab).value.trim();
  const dbAlias = document.getElementById("dropdown1").value;

  if (!queryText) {
    alert("Please enter a SQL query.");
    return;
  }

  document.getElementById("result").innerHTML = '<div class="loading">Running query...</div>';
  document.getElementById("columnResult").innerHTML = '<div class="loading">Running query...</div>';

  fetch("/runquery/execute_oracle_queries/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      script_name: dbAlias,
      query_sets: [[queryText]]
    })
  })
  .then(res => res.json())
  .then(data => {
    const result = data.results || data;
    document.getElementById("result").textContent = JSON.stringify(result, null, 2);
    const columnContainer = document.getElementById("columnResult");
    columnContainer.innerHTML = "";

    if (Array.isArray(result)) {
      result.forEach((entry, idx) => {
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
          const headers = Object.keys(queryResult[0]);
          const thead = document.createElement("thead");
          const headerRow = document.createElement("tr");

          headers.forEach(h => {
            const th = document.createElement("th");
            th.textContent = h;
            th.style.borderBottom = "1px solid var(--gray)";
            th.style.padding = "8px";
            th.style.background = "#f3f4f6";
            th.style.textAlign = "left";
            headerRow.appendChild(th);
          });

          thead.appendChild(headerRow);
          table.appendChild(thead);

          const tbody = document.createElement("tbody");
          queryResult.forEach(row => {
            const tr = document.createElement("tr");
            headers.forEach(h => {
              const td = document.createElement("td");
              td.textContent = row[h];
              td.style.padding = "8px";
              td.style.borderBottom = "1px solid #e5e7eb";
              tr.appendChild(td);
            });
            tbody.appendChild(tr);
          });

          table.appendChild(tbody);
          card.appendChild(table);
        } else {
          card.innerHTML += `<div style="color:gray">No rows returned</div>`;
        }

        columnContainer.appendChild(card);
      });
    }
  });
}

function fetchTableStructure(dbKey, refresh = false) {
  const url = `/runquery/get_table_structure/?db=${dbKey}${refresh ? '&refresh=1' : ''}`;
  fetch(url)
    .then(res => res.json())
    .then(data => {
      const sidebar = document.getElementById("tableStructure");
      sidebar.innerHTML = '';

      if (data.error) {
        sidebar.innerHTML = `<div style="color:red">${data.error}</div>`;
        return;
      }

      Object.entries(data.tables).forEach(([table, columns]) => {
        const box = document.createElement("details");
        box.className = "table-box";
        box.innerHTML = `<summary>📂 ${table}</summary>`;
        const ul = document.createElement("ul");
        columns.forEach(col => {
          const li = document.createElement("li");
          li.textContent = col;
          ul.appendChild(li);
        });
        box.appendChild(ul);
        sidebar.appendChild(box);
      });
    });
}

function refreshMetadata() {
  const dbKey = document.getElementById("dropdown1").value;
  fetchTableStructure(dbKey, true);
}
