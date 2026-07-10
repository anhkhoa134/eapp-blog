/**
* Custom Admin JS for eApp.vn Admin Panel
*/
(function() {
  "use strict";

  // Helper functions
  const select = (el, all = false) => {
    el = el.trim();
    if (all) {
      return [...document.querySelectorAll(el)];
    } else {
      return document.querySelector(el);
    }
  };

  const on = (type, el, listener, all = false) => {
    const selectEl = select(el, all);
    if (selectEl) {
      if (all) {
        selectEl.forEach(e => e.addEventListener(type, listener));
      } else {
        selectEl.addEventListener(type, listener);
      }
    }
  };

  const onscroll = (el, listener) => {
    el.addEventListener('scroll', listener);
  };

  // Sidebar toggle button behavior
  const backdrop = select('#sidebar-backdrop');

  function isMobile() {
    return window.innerWidth < 1200;
  }

  function closeSidebar() {
    const body = select('body');
    body.classList.remove('toggle-sidebar');
    const btn = select('.toggle-sidebar-btn');
    if (btn) {
      btn.classList.remove('bi-x');
      btn.classList.add('bi-list');
    }
    if (backdrop) {
      backdrop.classList.remove('show');
    }
  }

  if (select('.toggle-sidebar-btn')) {
    // Khởi tạo icon đúng khi tải trang
    const initBtn = select('.toggle-sidebar-btn');
    if (select('body').classList.contains('toggle-sidebar')) {
      initBtn.classList.remove('bi-list');
      initBtn.classList.add('bi-x');
    }

    on('click', '.toggle-sidebar-btn', function() {
      const body = select('body');
      body.classList.toggle('toggle-sidebar');
      // Đổi icon: bi-list <-> bi-x
      const isHidden = body.classList.contains('toggle-sidebar');
      this.classList.toggle('bi-list', !isHidden);
      this.classList.toggle('bi-x', isHidden);
      // Backdrop chỉ hiển thị trên mobile
      if (backdrop) {
        if (isHidden && isMobile()) {
          backdrop.classList.add('show');
        } else {
          backdrop.classList.remove('show');
        }
      }
    });
  }

  // Đóng sidebar khi nhấn vào backdrop
  if (backdrop) {
    backdrop.addEventListener('click', closeSidebar);
  }


  // Header scroll helper: adds shadow/transparency modifications when scrolled
  const selectHeader = select('#header');
  if (selectHeader) {
    const headerScrolled = () => {
      if (window.scrollY > 50) {
        selectHeader.classList.add('header-scrolled');
      } else {
        selectHeader.classList.remove('header-scrolled');
      }
    };
    window.addEventListener('load', headerScrolled);
    onscroll(document, headerScrolled);
  }

  // Back to top button visibility behavior
  const backtotop = select('.back-to-top');
  if (backtotop) {
    const toggleBacktotop = () => {
      if (window.scrollY > 100) {
        backtotop.classList.add('active');
      } else {
        backtotop.classList.remove('active');
      }
    };
    window.addEventListener('load', toggleBacktotop);
    onscroll(document, toggleBacktotop);
  }

  // Initialize Bootstrap Tooltips
  document.addEventListener("DOMContentLoaded", () => {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  });

  // Handle Form Validation triggers
  const needsValidation = document.querySelectorAll('.needs-validation');
  Array.prototype.slice.call(needsValidation).forEach(function(form) {
    form.addEventListener('submit', function(event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    }, false);
  });

  function closeSearchSelects(except) {
    document.querySelectorAll('.admin-search-select.is-open').forEach(function(wrapper) {
      if (wrapper !== except) {
        wrapper.classList.remove('is-open');
      }
    });
  }

  function initSearchSelects(scope) {
    const root = scope || document;
    root.querySelectorAll('select.form-control, select.form-select').forEach(function(selectEl) {
      if (selectEl.dataset.searchSelectReady === 'true' || selectEl.closest('.admin-search-select') || selectEl.multiple) {
        return;
      }

      const options = Array.from(selectEl.options);
      const shouldSearch = selectEl.dataset.searchable === 'true' || options.length > 8;
      const wrapper = document.createElement('div');
      wrapper.className = 'admin-search-select';
      if (selectEl.disabled) {
        wrapper.classList.add('is-disabled');
      }

      const trigger = document.createElement('button');
      trigger.type = 'button';
      trigger.className = 'admin-search-select__trigger';
      trigger.setAttribute('aria-haspopup', 'listbox');
      trigger.setAttribute('aria-expanded', 'false');

      const valueText = document.createElement('span');
      valueText.className = 'admin-search-select__value';
      const chevron = document.createElement('i');
      chevron.className = 'bi bi-chevron-down';
      trigger.append(valueText, chevron);

      const menu = document.createElement('div');
      menu.className = 'admin-search-select__menu';

      let searchInput = null;
      if (shouldSearch) {
        const searchWrap = document.createElement('div');
        searchWrap.className = 'admin-search-select__search';
        searchInput = document.createElement('input');
        searchInput.type = 'search';
        searchInput.placeholder = 'Tìm kiếm...';
        searchInput.autocomplete = 'off';
        searchWrap.appendChild(searchInput);
        menu.appendChild(searchWrap);
      }

      const list = document.createElement('div');
      list.className = 'admin-search-select__list';
      list.setAttribute('role', 'listbox');
      menu.appendChild(list);

      selectEl.classList.add('admin-native-select');
      selectEl.dataset.searchSelectReady = 'true';
      selectEl.parentNode.insertBefore(wrapper, selectEl);
      wrapper.append(selectEl, trigger, menu);

      function getSelectedOption() {
        return selectEl.options[selectEl.selectedIndex] || selectEl.options[0];
      }

      function updateValue() {
        const selected = getSelectedOption();
        valueText.textContent = selected ? selected.text : '';
        valueText.classList.toggle('is-placeholder', !selected || selected.value === '');
      }

      function renderOptions(query) {
        const normalizedQuery = (query || '').trim().toLowerCase();
        list.innerHTML = '';

        Array.from(selectEl.options).forEach(function(option) {
          const optionText = option.text || '';
          if (normalizedQuery && !optionText.toLowerCase().includes(normalizedQuery)) {
            return;
          }

          const item = document.createElement('button');
          item.type = 'button';
          item.className = 'admin-search-select__option';
          item.setAttribute('role', 'option');
          item.setAttribute('aria-selected', option.selected ? 'true' : 'false');
          item.dataset.value = option.value;

          const check = document.createElement('i');
          check.className = option.selected ? 'bi bi-check-lg' : 'bi';
          const label = document.createElement('span');
          label.textContent = optionText;
          item.append(check, label);

          item.addEventListener('click', function() {
            selectEl.value = option.value;
            selectEl.dispatchEvent(new Event('change', { bubbles: true }));
            updateValue();
            renderOptions(searchInput ? searchInput.value : '');
            wrapper.classList.remove('is-open');
            trigger.setAttribute('aria-expanded', 'false');
            trigger.focus();
          });

          list.appendChild(item);
        });

        if (!list.children.length) {
          const empty = document.createElement('div');
          empty.className = 'admin-search-select__empty';
          empty.textContent = 'Không có kết quả';
          list.appendChild(empty);
        }
      }

      trigger.addEventListener('click', function() {
        if (selectEl.disabled) {
          return;
        }
        const willOpen = !wrapper.classList.contains('is-open');
        closeSearchSelects(wrapper);
        wrapper.classList.toggle('is-open', willOpen);
        trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
        if (willOpen) {
          renderOptions(searchInput ? searchInput.value : '');
          if (searchInput) {
            setTimeout(function() {
              searchInput.focus();
              searchInput.select();
            }, 0);
          }
        }
      });

      if (searchInput) {
        searchInput.addEventListener('input', function() {
          renderOptions(searchInput.value);
        });
        searchInput.addEventListener('keydown', function(event) {
          if (event.key === 'Escape') {
            wrapper.classList.remove('is-open');
            trigger.setAttribute('aria-expanded', 'false');
            trigger.focus();
          }
        });
      }

      selectEl.addEventListener('change', function() {
        updateValue();
        renderOptions(searchInput ? searchInput.value : '');
      });

      const observer = new MutationObserver(function() {
        updateValue();
        renderOptions(searchInput ? searchInput.value : '');
      });
      observer.observe(selectEl, { childList: true, subtree: true, attributes: true, attributeFilter: ['selected', 'disabled'] });

      updateValue();
      renderOptions('');
    });
  }

  document.addEventListener('click', function(event) {
    if (!event.target.closest('.admin-search-select')) {
      closeSearchSelects();
    }
  });

  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
      closeSearchSelects();
    }
  });

  document.addEventListener('DOMContentLoaded', function() {
    initSearchSelects(document);
  });

  // Init via htmx:load (after the settle phase) instead of htmx:afterSwap:
  // during settling htmx resets class/style on id-matched elements to the
  // server-sent values, which would strip the .admin-native-select class
  // added here and reveal the native select next to the custom widget.
  if (window.htmx) {
    htmx.onLoad(function(content) {
      initSearchSelects(content);
    });
  }

  // Auto-resize active echarts dynamically on sidebar expand/collapse or window resize
  const mainContainer = select('#main');
  if (mainContainer && typeof echarts !== 'undefined') {
    setTimeout(() => {
      const resizeObserver = new ResizeObserver(function() {
        const echartsList = select('.echart', true);
        echartsList.forEach(getEchart => {
          const chart = echarts.getInstanceByDom(getEchart);
          if (chart) {
            chart.resize();
          }
        });
      });
      resizeObserver.observe(mainContainer);
    }, 200);
  }

})();
