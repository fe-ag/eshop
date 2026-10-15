(function () {
  'use strict';

  // Sidebar toggle (mobile)
  var sidebar = document.getElementById('sidebar');
  var menuBtn = document.querySelector('[data-sidebar-toggle]');
  if (sidebar && menuBtn) {
    menuBtn.addEventListener('click', function () {
      var open = sidebar.classList.toggle('is-open');
      menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Confirmation for forms that carry data-confirm
  document.querySelectorAll('form[data-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (!window.confirm(form.getAttribute('data-confirm'))) { event.preventDefault(); }
    });
  });

  // Inline formsets: "Add another row"
  document.querySelectorAll('[data-formset]').forEach(function (box) {
    var prefix = box.getAttribute('data-prefix');
    var total = box.querySelector('input[name="' + prefix + '-TOTAL_FORMS"]');
    var body = box.querySelector('[data-formset-body]');
    var template = box.querySelector('[data-formset-template]');
    var addBtn = box.querySelector('[data-formset-add]');
    if (!total || !body || !template || !addBtn) { return; }
    addBtn.addEventListener('click', function () {
      var index = parseInt(total.value, 10);
      var html = template.innerHTML.replace(/__prefix__/g, String(index));
      var holder = document.createElement('table');
      holder.innerHTML = '<tbody>' + html + '</tbody>';
      var row = holder.querySelector('tr');
      if (row) { body.appendChild(row); total.value = String(index + 1); }
    });
  });

  // Appearance page: presets, live preview, discard
  var form = document.getElementById('appearance-form');
  var preview = document.getElementById('theme-preview');
  var presetsEl = document.getElementById('presets-data');
  var fontsEl = document.getElementById('fonts-data');
  if (form && preview && presetsEl && fontsEl) {
    var presets = JSON.parse(presetsEl.textContent);
    var fonts = JSON.parse(fontsEl.textContent);

    var applyVar = function (input) {
      var name = input.getAttribute('data-css-var');
      if (!name || input.value === '') { return; }
      var unit = input.getAttribute('data-unit') || '';
      preview.style.setProperty(name, input.value + unit);
    };
    var applyFont = function (select, variable) {
      var stack = fonts[select.value] || fonts.system;
      preview.style.setProperty(variable, stack);
    };
    var refresh = function () {
      form.querySelectorAll('[data-css-var]').forEach(applyVar);
      var body = form.querySelector('[name="body_font"]');
      var heading = form.querySelector('[name="heading_font"]');
      if (body) { applyFont(body, '--f-body'); }
      if (heading) { applyFont(heading, '--f-heading'); }
    };

    form.addEventListener('input', refresh);
    form.addEventListener('change', refresh);

    var profile = form.querySelector('[name="profile_name"]');
    if (profile) {
      profile.addEventListener('change', function () {
        var data = presets[profile.value];
        if (!data) { return; }
        Object.keys(data).forEach(function (key) {
          var input = form.querySelector('[name="' + key + '"]');
          if (input) { input.value = data[key]; }
        });
        refresh();
      });
    }
    var discard = form.querySelector('[data-discard]');
    if (discard) {
      discard.addEventListener('click', function () { window.setTimeout(refresh, 0); });
    }
    refresh();
  }
})();
