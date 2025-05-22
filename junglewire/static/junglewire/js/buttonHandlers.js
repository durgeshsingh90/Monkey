const exclusiveButtons = ['dev77', 'paypal77', 'novate', 'test77', 'cert77', 'netscaler'];

exclusiveButtons.forEach(id => {
  document.getElementById(id).addEventListener('click', function () {
    exclusiveButtons.forEach(btnId => {
      document.getElementById(btnId).classList.remove('active');
    });
    this.classList.add('active');
  });
});

['updateBtn', 'echoBtn', 'incrBtn'].forEach(id => {
  document.getElementById(id).addEventListener('click', function () {
    this.classList.toggle('active');
  });
});
