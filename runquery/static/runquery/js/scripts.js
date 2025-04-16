const tabButtons = document.querySelectorAll(".tab-button");
const tabContents = document.querySelectorAll(".tab-content");
const textareas = document.querySelectorAll("textarea");
let scriptData = {};

function showTab(index) {
  tabButtons.forEach(btn => btn.classList.remove("active"));
  tabContents.forEach(tab => tab.classList.remove("active"));
  tabButtons[index].classList.add("active");
  tabContents[index].classList.add("active");
  localStorage.setItem("activeTab", index);
}

tabButtons.forEach(btn => {
  btn.addEventListener("click", () => showTab(parseInt(btn.dataset.index)));
});

textareas.forEach((textarea, idx) => {
  const saved = localStorage.getItem(`text-${idx}`);
  if (saved) textarea.value = saved;
  textarea.addEventListener("input", () => {
    localStorage.setItem(`text-${idx}`, textarea.value);
  });
});

async function execute() {
  const queries = {};
  textareas.forEach((ta, idx) => queries[`tab${idx}`] = ta.value);

  const formData = new FormData();
  formData.append("queries", JSON.stringify(queries));

  await fetch("/runquery/submit/", { method: "POST", body: formData });
  alert("✅ Sent to backend.");
}

function countChars() {
  const current = document.querySelector(".tab-content.active textarea");
  alert("Characters: " + current.value.length);
}

async function saveScript() {
  const name = document.getElementById("scriptName").value.trim();
  const folder = document.getElementById("folderName").value;

  if (!name) return alert("Enter a script name");

  const tabs = {};
  textareas.forEach((ta, idx) => tabs[`tab${idx}`] = ta.value);

  await fetch("/runquery/save_script/", {
    method: "POST",
    body: JSON.stringify({ name, folder, tabs })
  });

  alert("✅ Script saved!");
  loadScripts();
}

async function loadScripts() {
  const res = await fetch("/runquery/load_scripts/");
  const data = await res.json();
  scriptData = data.scripts;

  const select = document.getElementById("scriptSelect");
  select.innerHTML = '<option value="">-- Select Script --</option>';

  for (const folder in scriptData) {
    const group = document.createElement("optgroup");
    group.label = folder;

    scriptData[folder].forEach(script => {
      const opt = document.createElement("option");
      opt.value = `${folder}::${script.name}`;
      opt.textContent = script.name;
      group.appendChild(opt);
    });

    select.appendChild(group);
  }
}

function loadScript() {
  const val = document.getElementById("scriptSelect").value;
  if (!val.includes("::")) return;

  const [folder, name] = val.split("::");
  const script = scriptData[folder].find(s => s.name === name);
  if (!script) return;

  textareas.forEach((ta, idx) => {
    const key = `tab${idx}`;
    ta.value = script.tabs[key] || "";
    localStorage.setItem(`text-${idx}`, ta.value);
  });
}

function filterScripts() {
  const filter = document.getElementById("searchScript").value.toLowerCase();
  const select = document.getElementById("scriptSelect");

  Array.from(select.options).forEach(opt => {
    if (!opt.value.includes("::")) return;
    opt.style.display = opt.textContent.toLowerCase().includes(filter) ? "" : "none";
  });
}

window.onload = () => {
  loadScripts();
  showTab(parseInt(localStorage.getItem("activeTab") || 0));
};
