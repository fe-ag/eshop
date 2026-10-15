(function () {
  'use strict';

  // Mobile navigation toggle
  var navToggle = document.querySelector('[data-nav-toggle]');
  var nav = document.getElementById('main-nav');
  if (navToggle && nav) {
    navToggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Auto-submit the sort selector on the product list
  var sort = document.getElementById('f-sort');
  if (sort && sort.form) {
    sort.addEventListener('change', function () { sort.form.submit(); });
  }

  // Product gallery thumbnails
  var gallery = document.querySelector('[data-gallery]');
  if (gallery) {
    var mainImg = document.getElementById('gallery-main-img');
    gallery.querySelectorAll('.thumb').forEach(function (thumb) {
      thumb.addEventListener('click', function () {
        mainImg.src = thumb.getAttribute('data-src');
        mainImg.alt = thumb.getAttribute('data-alt') || '';
        gallery.querySelectorAll('.thumb').forEach(function (t) { t.classList.remove('is-active'); });
        thumb.classList.add('is-active');
      });
    });
  }

  // Variant picker: update price, stock text and the add-to-cart button.
  // (The server re-validates price, stock and the variant id on every request.)
  var buyForm = document.querySelector('[data-buy-form]');
  if (buyForm) {
    var currency = buyForm.getAttribute('data-currency') || '';
    var priceNow = buyForm.querySelector('[data-price-now]');
    var priceOld = buyForm.querySelector('[data-price-old]');
    var stockText = buyForm.querySelector('[data-stock-text]');
    var addBtn = buyForm.querySelector('[data-add-btn]');
    var qty = buyForm.querySelector('[data-qty]');
    var money = function (value) {
      var number = parseFloat(value);
      if (isNaN(number)) { return ''; }
      return currency + number.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    };
    var update = function () {
      var checked = buyForm.querySelector('input[name="variant_id"]:checked');
      if (!checked) { return; }
      var stock = parseInt(checked.getAttribute('data-stock'), 10) || 0;
      priceNow.textContent = money(checked.getAttribute('data-price'));
      var old = checked.getAttribute('data-old');
      if (old) { priceOld.textContent = money(old); priceOld.hidden = false; } else { priceOld.hidden = true; }
      stockText.textContent = '';
      var span = document.createElement('span');
      if (stock > 0) {
        span.className = 'in-stock';
        span.textContent = stock <= 5 ? 'In stock - only ' + stock + ' left' : 'In stock';
      } else {
        span.className = 'out-stock';
        span.textContent = 'Out of stock';
      }
      stockText.appendChild(span);
      addBtn.disabled = stock <= 0;
      if (qty) {
        var limit = Math.max(1, Math.min(stock || 1, parseInt(qty.getAttribute('data-limit') || qty.max || '10', 10)));
        if (!qty.getAttribute('data-limit')) { qty.setAttribute('data-limit', qty.max || '10'); }
        qty.max = String(limit);
        if (parseInt(qty.value, 10) > limit) { qty.value = String(limit); }
      }
    };
    buyForm.querySelectorAll('input[name="variant_id"]').forEach(function (input) {
      input.addEventListener('change', update);
    });
    update();
  }
})();
