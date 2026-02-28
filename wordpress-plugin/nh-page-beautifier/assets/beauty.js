(function () {
  'use strict';

  function initFaq(root) {
    var toggles = root.querySelectorAll('.nhpb-faq-q');
    toggles.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var item = btn.closest('.nhpb-faq-item');
        var open = item.classList.contains('is-open');
        item.classList.toggle('is-open', !open);
        btn.setAttribute('aria-expanded', String(!open));
      }, { passive: true });
    });
  }

  function initReveal(root) {
    var items = root.querySelectorAll('.nhpb-reveal');
    if (!('IntersectionObserver' in window) || !items.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12 });
    items.forEach(function (el) { io.observe(el); });
  }

  function boot() {
    document.querySelectorAll('.nhpb-root').forEach(function (root) {
      initFaq(root);
      initReveal(root);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
