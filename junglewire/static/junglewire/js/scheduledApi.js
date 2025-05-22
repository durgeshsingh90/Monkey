document.getElementById('scheduledBtn').addEventListener('click', () => {
  fetch('/api/schedule/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({
      action: 'schedule_now',
      testcases: [...selectedTestCases].map(JSON.parse)
    })
  })
    .then(res => res.ok ? res.json() : Promise.reject('Failed'))
    .then(data => alert('Scheduled: ' + data.message))
    .catch(err => {
      console.error(err);
      alert('Scheduling failed.');
    });
});

function getCSRFToken() {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}
