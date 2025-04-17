
let calendar;

document.addEventListener("DOMContentLoaded", function () {
  loadConfig();
  setupDatePicker();
  initCalendar();
});
$(document).ready(function() {
$('#psp').select2({
placeholder: 'Select a PSP',
allowClear: true,
width: 'resolve'
});
});

function getCSRFToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function loadConfig() {
  fetch('/slot_booking/config.json')
    .then(response => response.json())
    .then(config => {
      populateSelect('psp', config.psps, false, false, false, false, false, true);
      populateSelect('owner', config.owners, false, true);
      populateSelect('server', config.servers, false, false, true);
      populateSelect('schemeType', config.schemeTypes, true, false, false, true);
      populateSelect('simulator', config.simulators, false, false, false, false, true);
    });
}
function setupDatePicker() {
  flatpickr("#dateRange", {
    mode: "range",
    dateFormat: "d/m/Y",
    allowInput: true,
    autoApply: true,
    onChange: function(selectedDates, dateStr, instance) {
      if (selectedDates.length === 1) {
        const formatted = instance.formatDate(selectedDates[0], "d/m/Y");
        instance.input.value = `${formatted} to ${formatted}`;
      }
    },
    onClose: function(selectedDates, dateStr, instance) {
      if (selectedDates.length === 1) {
        const formatted = instance.formatDate(selectedDates[0], "d/m/Y");
        instance.input.value = `${formatted} to ${formatted}`;
      } else if (selectedDates.length === 2) {
        const start = instance.formatDate(selectedDates[0], "d/m/Y");
        const end = instance.formatDate(selectedDates[1], "d/m/Y");
        instance.input.value = `${start} to ${end}`;
      }
    }
  });
}



function populateSelect(elementId, options, isMultiple = false, isOwner = false, isServer = false, isSchemeType = false, isSimulator = false, isPSP = false) {
  const selectElement = document.getElementById(elementId);
  selectElement.innerHTML = "";

  options.forEach(option => {
    const opt = document.createElement('option');

    if (isPSP) {
      opt.value = JSON.stringify(option);
      opt.text = `${option.name} (${option.pspID})`;
    } else if (isOwner) {
      opt.value = JSON.stringify(option);
      opt.text = option.name;  // ✅ Only display name, not LAN ID    
    } else if (isServer) {
      opt.value = JSON.stringify(option);
      opt.text = `${option.hostname} (${option.user})`;
    } else if (isSimulator) {
      opt.value = JSON.stringify(option);
      opt.text = `${option.name} (${option.ipAddress})`;
    } else if (isSchemeType) {
      opt.value = option.name;
      opt.text = option.name;
    } else {
      opt.value = option.name || option.hostname || option.pspID || option.lanID;
      opt.text = option.name || option.hostname || option.pspID || option.lanID;
    }

    selectElement.add(opt);
  });

  if (elementId === 'psp') {
    $('#psp').select2({
      placeholder: 'Select a PSP',
      allowClear: true,
      width: 'resolve'
    });
  }
}


function validateForm() {
  const requiredFields = ['projectName', 'psp', 'owner', 'schemeType', 'simulator', 'dateRange'];
  for (let field of requiredFields) {
    if (!document.getElementById(field).value) {
      document.getElementById('submissionMessage').textContent = 'Please fill out all required fields';
      document.getElementById('submissionMessage').style.color = 'red';
      return false;
    }
  }

  const serverValue = document.getElementById('server').value;
  if (!serverValue) {
    document.getElementById('submissionMessage').textContent = 'Please select a server';
    document.getElementById('submissionMessage').style.color = 'red';
    return false;
  }

  const timeSlots = document.querySelectorAll('input[name="timeSlot"]:checked').length;
  if (!timeSlots) {
    document.getElementById('submissionMessage').textContent = 'Select at least one Time Slot';
    document.getElementById('submissionMessage').style.color = 'red';
    return false;
  }

  return true;
}

function submitForm() {
  if (!validateForm()) return;
  
  const form = document.getElementById('projectForm');
  const formData = new FormData(form);
  const dateRange = formData.get('dateRange');
  const dateRangeArray = dateRange ? dateRange.split(" to ") : [];

  const jsonData = {
    projectName: formData.get('projectName'),
    projectID: formData.get('projectID') || "",
    psp: JSON.parse(formData.get('psp')),
    comments: formData.get('comments') || "",
    owner: JSON.parse(formData.get('owner')),
    server: JSON.parse(formData.get('server')),
    schemeType: formData.getAll('schemeType'),
    simulator: JSON.parse(formData.get('simulator')),
    dateRange: {
      start: dateRangeArray[0] || "",
      end: dateRangeArray[1] || (dateRangeArray[0] || "") // handle single date case
    },
    timeSlot: formData.getAll('timeSlot'),
    openSlot: formData.has('openSlot')
  };

  const csrfToken = getCSRFToken();
  const submitButton = document.getElementById('submitButton');

  fetch('/slot_booking/submit/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    },
    body: JSON.stringify(jsonData)
  })
  .then(response => response.json())
  .then(data => {
    if (data.bookingID) {
      document.getElementById('submissionMessage').textContent = `✅ Submission saved! Booking ID: ${data.bookingID}`;
      document.getElementById('submissionMessage').style.color = 'green';
      submitButton.textContent = 'Booked';
      submitButton.style.backgroundColor = 'green';
      setTimeout(() => location.reload(), 1000);
    } else {
      throw new Error(data.error || 'Unknown error occurred');
    }
  })
  .catch(error => {
    document.getElementById('submissionMessage').textContent = `Error: ${error.message}`;
    document.getElementById('submissionMessage').style.color = 'red';
    submitButton.textContent = 'Error';
    submitButton.style.backgroundColor = 'red';
    setTimeout(() => {
      submitButton.textContent = 'Submit';
      submitButton.style.backgroundColor = '';
    }, 1000);
  });
}


function goToSettings() {
window.location.href = "/slot_booking/admin/";
}


function initCalendar() {
  const calendarEl = document.getElementById('calendar');

  calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'yearButton,dayGridMonth,timeGridWeek,timeGridDay'
    },
    customButtons: {
      yearButton: {
        text: 'year',
        click: function () {
          const date = calendar.getDate();
          const yearStart = new Date(date.getFullYear(), 0, 1);
          calendar.changeView('multiMonthYear', { date: yearStart });
        }
      }
    },
    views: {
      multiMonthYear: {
        type: 'multiMonth',
        duration: { years: 1 },
        multiMonthMaxColumns: 3,
        multiMonthMinWidth: 150
      }
    },
    events: fetchEvents,
    dateClick: function (info) {
      if (info.view.type === 'multiMonthYear') {
        calendar.changeView('dayGridMonth', info.date);
      }
    },
    eventContent: function (arg) {
      const sub = arg.event.extendedProps;
      const viewType = arg.view.type;
      let colorClass = sub.openSlot ? 'open-slot-color' : '';

      if (!sub.openSlot) {
        if (sub.timeSlot.includes('morning')) colorClass = 'morning-slot';
        else if (sub.timeSlot.includes('afternoon')) colorClass = 'afternoon-slot';
        else if (sub.timeSlot.includes('overnight')) colorClass = 'overnight-slot';
      }

      if (sub.status === 'Cancelled') {
        colorClass = 'cancelled-slot';
      }

      const serverText = Array.isArray(sub.server)
        ? sub.server.map(s => s.user).join("/")
        : (sub.server?.user || 'N/A');

      const baseTitle = sub.openSlot
        ? 'Open Slot'
        : `${sub.bookingID} - ${serverText} - ${sub.schemeType.join("/")} - ${sub.simulator.name}`;

      const title = sub.status === 'Cancelled'
        ? `❌ <del>${baseTitle}</del>`
        : baseTitle;

      return viewType === 'multiMonthYear'
        ? { html: `<div class="event-dot ${colorClass}"></div>` }
        : { html: `<div class="event-bar ${colorClass}">${title}</div>` };
    },

    eventMouseEnter: function (info) {
      const sub = info.event.extendedProps;
    
      const tooltip = document.createElement('div');
      tooltip.className = 'tooltip';
      tooltip.innerHTML = `
        <strong>Booking ID:</strong> ${sub.bookingID}<br>
        <strong>Project Name:</strong> ${sub.projectName}<br>
        <strong>Project ID:</strong> ${sub.projectID || 'N/A'}<br>
        <strong>PSP:</strong> ${sub.psp.name} (${sub.psp.pspID})<br>
        <strong>Owner:</strong> ${sub.owner.name} (${sub.owner.lanID || ''})<br>
        <strong>Server:</strong> ${
          Array.isArray(sub.server)
            ? sub.server.map(s => `${s.hostname} (${s.user})`).join('<br>')
            : (sub.server?.hostname ? `${sub.server.hostname} (${sub.server.user})` : 'N/A')
        }<br>
        <strong>Schemes:</strong> ${sub.schemeType.join(", ")}<br>
        <strong>Simulator:</strong> ${sub.simulator.name} (${sub.simulator.ipAddress})<br>
        <strong>Time Slots:</strong> ${sub.timeSlot.join(", ")}<br>
        <strong>Date Range:</strong> ${sub.dateRange.start} to ${sub.dateRange.end}<br>
        <strong>Open Slot:</strong> ${sub.openSlot ? 'Yes' : 'No'}<br>
        <strong>Comments:</strong> ${sub.comments || 'N/A'}
      `;
      document.body.appendChild(tooltip);
    
      // Positioning
      const moveTooltip = (e) => {
        tooltip.style.left = e.pageX + 10 + 'px';
        tooltip.style.top = e.pageY + 10 + 'px';
      };
      info.el.addEventListener('mousemove', moveTooltip);
    
      // Flags to track hover state
      let stillOnTooltip = false;
      let stillOnEvent = true;
    
      // Tooltip hover
      tooltip.addEventListener('mouseenter', () => stillOnTooltip = true);
      tooltip.addEventListener('mouseleave', () => {
        stillOnTooltip = false;
        setTimeout(() => {
          if (!stillOnTooltip && !stillOnEvent) tooltip.remove();
        }, 100);
      });
    
      // Event hover
      info.el.addEventListener('mouseleave', () => {
        stillOnEvent = false;
        setTimeout(() => {
          if (!stillOnTooltip && !stillOnEvent) tooltip.remove();
        }, 100);
      });
    }
,    
    

    eventDidMount: function (info) {
      info.el.addEventListener('dblclick', function () {
        const bookingID = info.event.extendedProps.bookingID;
        const status = info.event.extendedProps.status;

        if (status === 'Cancelled') {
          alert(`Booking ID ${bookingID} is already cancelled.`);
          return;
        }

        if (confirm(`Do you want to cancel booking ID ${bookingID}?`)) {
          cancelBooking(bookingID);
        }
      });
    }
  });

  calendar.render();
}


function fetchEvents(fetchInfo, successCallback, failureCallback) {
  fetch('/slot_booking/submissions/')
    .then(response => response.json())
    .then(data => {
      const events = [];
      data.submissions.forEach(sub => {
        const isOpenSlot = sub.openSlot === true;
        if (isOpenSlot) {
          const startDate = parseDate(sub.dateRange.start);
          const endDate = parseDate(sub.dateRange.end);
          let currentDate = new Date(startDate);
          while (currentDate <= endDate) {
            const day = currentDate.getDay();
            if (day === 2 || day === 4) {
              events.push({
                id: sub.bookingID,
                title: 'Open Slot',
                start: formatDateToISO(currentDate),
                extendedProps: { ...sub, openSlot: true }
              });
            }
            currentDate.setDate(currentDate.getDate() + 1);
          }
        } else {
          const serverTitle = Array.isArray(sub.server)
  ? sub.server.map(s => s.user).join("/")
  : (sub.server?.user || 'N/A');

          events.push({
            id: sub.bookingID,
            title: `${sub.bookingID} - ${serverTitle} - ${sub.schemeType.join("/")} - ${sub.simulator.name}`,
            start: formatDate(sub.dateRange.start),
            end: formatDate(sub.dateRange.end, true),
            extendedProps: { ...sub, openSlot: false }
          });
        }
      });
      successCallback(events);
    })
    .catch(error => failureCallback(error));
}

function parseDate(dateStr) {
  if (!dateStr) return null;
  const [day, month, year] = dateStr.split('/');
  return new Date(year, month - 1, day);
}

function formatDateToISO(dateObj) {
  if (!dateObj) return null;
  return `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}-${String(dateObj.getDate()).padStart(2, '0')}`;
}

function formatDate(dateStr, addOneDay = false) {
  const date = parseDate(dateStr);
  if (addOneDay && date) date.setDate(date.getDate() + 1);
  return formatDateToISO(date);
}


function globalSearch() {
  const searchInput = document.getElementById('globalSearchInput').value.trim().toLowerCase();
  if (!searchInput) {
    document.getElementById('searchResult').innerHTML = '<span style="color:red;">Please enter a search term.</span>';
    return;
  }

  fetch('/slot_booking/submissions/')
    .then(response => response.json())
    .then(data => {
      const matchedBookings = data.submissions.filter(sub => {
        const fieldsToSearch = [
          sub.bookingID.toString(),
          sub.projectName,
          sub.projectID || '',
          sub.psp.name || '',
          sub.psp.pspID || '',
          sub.owner.name || '',
          sub.owner.lanID || '',
          sub.server.hostname || '',
          sub.server.user || '',
          sub.schemeType.join(' '),
          sub.simulator.name || '',
          sub.simulator.ipAddress || '',
          sub.comments || '',
          sub.dateRange.start || '',
          sub.dateRange.end || '',
          sub.timeSlot.join(' '),
          sub.openSlot ? 'yes' : 'no'
        ];
        return fieldsToSearch.join(' ').toLowerCase().includes(searchInput);
      });

      if (matchedBookings.length > 0) {
        // Sort descending by bookingID
        matchedBookings.sort((a, b) => b.bookingID - a.bookingID);
      
        let resultHtml = `<strong>Found ${matchedBookings.length} result(s):</strong><br><br>`;
      
        matchedBookings.forEach(sub => {
          resultHtml += `
            <div style="border: 1px solid #ddd; padding: 10px; border-radius: 4px; background: #f9f9f9; margin-bottom: 10px;">
              <strong>Booking ID:</strong> ${sub.bookingID}<br>
              <strong>Project Name:</strong> ${sub.projectName}<br>
              <strong>Project ID:</strong> ${sub.projectID || 'N/A'}<br>
              <strong>PSP:</strong> ${sub.psp.name} (${sub.psp.pspID})<br>
              <strong>Owner:</strong> ${sub.owner.name} (${sub.owner.lanID})<br>
              <strong>Server:</strong> ${sub.server.hostname} (${sub.server.user})<br>
              <strong>Schemes:</strong> ${sub.schemeType.join(", ")}<br>
              <strong>Simulator:</strong> ${sub.simulator.name} (${sub.simulator.ipAddress})<br>
              <strong>Time Slots:</strong> ${sub.timeSlot.join(", ")}<br>
              <strong>Date Range:</strong> ${sub.dateRange.start} to ${sub.dateRange.end}<br>
              <strong>Open Slot:</strong> ${sub.openSlot ? 'Yes' : 'No'}<br>
              <strong>Comments:</strong> ${sub.comments || 'N/A'}
            </div>
          `;
        });
        document.getElementById('searchResult').innerHTML = resultHtml;
      } else {
        document.getElementById('searchResult').innerHTML = `<span style="color:red;">No results found for "${searchInput}".</span>`;
      }
    });
}

function clearSearch() {
  location.reload(); // Reloads the current page
}


function cancelBooking(bookingID) {
  fetch(`/slot_booking/cancel/${bookingID}/`, {
    method: 'POST',
    headers: {
      'X-CSRFToken': getCSRFToken(),
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.message) {
      alert(data.message);
      calendar.refetchEvents(); // Refresh the calendar events
    } else {
      alert(data.error || "Failed to cancel booking.");
    }
  })
  .catch(error => {
    console.error(error);
    alert("An error occurred while cancelling the booking.");
  });
}

document.getElementById("globalSearchInput").addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    event.preventDefault();  // Prevent form submission or page reload
    globalSearch();          // Trigger the search
  }
});
