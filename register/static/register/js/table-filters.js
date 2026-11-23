/* =============================================================================
   Per-column popover filters + drag-to-reorder for the admin DataTables.

   One implementation shared by every list page. A table opts in with:

     const dt = new DataTable('#myTable', Object.assign({
       ...                                  // the page's own options
     }, RegisterTable.options({ fixedLeft: 1, fixedRight: 1 })));
     RegisterTable.enhance(dt);             // in initComplete, or straight after

   and by tagging its headings:

     <th data-col-key="title"  data-filter="text">Title</th>
     <th data-col-key="start"  data-filter="date">Start Date</th>
     <th data-col-key="total"  data-filter="number">Total</th>
     <th data-col-key="status" data-filter="choice"
         data-choices="Active,Inactive">Status</th>     <!-- choices optional -->

   A heading with no data-filter (checkbox / action columns) gets no funnel.

   Notes that matter if you touch this:

   * With scrollX/scrollY DataTables renders the VISIBLE heading in its own
     table, which carries no id — so headings come from the API
     (columns().header()), never from a `#table thead th` selector. FixedHeader
     clones the heading again while scrolled, which is why every handler here is
     delegated on document rather than bound per button.
   * Bootstrap's popover sanitiser strips <input>. sanitize:false is required;
     every node in a popover is built here, never from user content.
   * flatpickr renders after Bootstrap has measured and positioned the popover,
     so the date popover reserves the calendar's width up front (see the
     .filter-pop-date rule in table-filters.css). Squeezing the calendar into a
     narrow popover silently clips Friday and Saturday off the grid.
   ========================================================================== */
(function (window, document) {
  'use strict';

  // Registry so the global DataTables search hook can find the right table.
  const TABLES = {};

  const DATE_MODES = [
    { id: 'eq',      label: 'Is on',   first: 'Date',             second: null },
    { id: 'before',  label: 'Before',  first: 'Before this date', second: null },
    { id: 'after',   label: 'After',   first: 'After this date',  second: null },
    { id: 'between', label: 'Between', first: 'From',             second: 'To' },
  ];

  const FUNNEL_SVG =
    '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
    '<path fill="currentColor" d="M4 5h16l-6.2 7.2v5.3l-3.6 2v-7.3z"/></svg>';

  function escapeRegex(s) {
    return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function textOf(node) {
    return node ? String(node.textContent || '').replace(/\s+/g, ' ').trim() : '';
  }

  /* Every date this app renders starts with an ISO day (Y-m-d h:i A, or
     %Y-%m-%d %I:%M %p from the ajax endpoints), so the day can be read straight
     out of the cell. data-date on the cell wins when it is there. */
  function dateOf(node) {
    if (!node) return '';
    if (node.dataset && node.dataset.date) return node.dataset.date;
    const m = textOf(node).match(/\d{4}-\d{2}-\d{2}/);
    return m ? m[0] : '';
  }

  function numberOf(node) {
    if (!node) return null;
    if (node.dataset && node.dataset.num) {
      const d = parseFloat(node.dataset.num);
      return isNaN(d) ? null : d;
    }
    // Strip currency symbols and thousands separators, keep one sign/decimal.
    const t = textOf(node).replace(/[^0-9.\-]/g, '');
    if (!t || t === '-' || t === '.') return null;
    const v = parseFloat(t);
    return isNaN(v) ? null : v;
  }

  /* A heading may prefix its label with a group tag (Player / Contact /
     Billing on the golf entries table); the chip reads better qualified. */
  function labelOf(th) {
    if (th.dataset.label) return th.dataset.label;
    const flat = textOf(th);
    const tag = th.querySelector('.grp-tag');
    if (!tag) return flat;
    const name = textOf(tag);
    return name + ' \u2014 ' + flat.slice(name.length).trim();
  }

  function dateMatches(v, f) {
    switch (f.mode) {
      case 'eq':     return v === f.from;
      case 'before': return v < f.from;                  // strictly earlier
      case 'after':  return v > f.from;                  // strictly later
      default:                                            // between, inclusive
        return (!f.from || v >= f.from) && (!f.to || v <= f.to);
    }
  }

  function enhance(api, opts) {
    opts = opts || {};
    const table = api.table().node();
    const tableId = table.id;
    const STATE = {};
    let OPEN = null, OPEN_KEY = null;

    /* ---------- column lookup, always by key ---------- */
    // Dragging a heading changes every index after it, so nothing here may
    // remember an index.
    function eachColumn(fn) {
      api.columns().every(function (i) {
        fn.call(this, this.header(), i);
        return true;
      });
    }

    function colIndex(key) {
      let found = -1;
      eachColumn(function (th, i) {
        if (th && th.dataset && th.dataset.colKey === key) found = i;
      });
      return found;
    }

    function headerFor(key) {
      let th = null;
      eachColumn(function (h) {
        if (h && h.dataset.colKey === key) th = h;
      });
      return th;
    }

    function cellNode(rowIdx, key) {
      const i = colIndex(key);
      if (i < 0) return null;
      try { return api.cell(rowIdx, i).node(); } catch (e) { return null; }
    }

    /* ---------- the row-level filter (dates and numbers) ---------- */
    // column().search() can only match the cell's text, so anything comparing
    // magnitudes has to run as a row filter instead.
    TABLES[tableId] = function (rowIdx) {
      return Object.keys(STATE).every(function (key) {
        const f = STATE[key];
        if (!f) return true;
        if (f.type === 'date') {
          const v = dateOf(cellNode(rowIdx, key));
          return v ? dateMatches(v, f.value) : false;   // no date matches nothing
        }
        if (f.type === 'number') {
          const v = numberOf(cellNode(rowIdx, key));
          if (v === null) return false;
          if (f.value.min !== undefined && v < f.value.min) return false;
          if (f.value.max !== undefined && v > f.value.max) return false;
          return true;
        }
        return true;
      });
    };

    /* ---------- applying ---------- */
    function applyFilters() {
      Object.keys(STATE).forEach(function (key) {
        const f = STATE[key];
        const i = colIndex(key);
        if (i < 0) return;
        if (f.type === 'text') {
          api.column(i).search(f.value, false, false, true);
        } else if (f.type === 'choice') {
          // Whole-cell match, so "Active" never drags "Inactive" in with it.
          api.column(i).search('^\\s*(' + f.value.map(escapeRegex).join('|') + ')\\s*$', true, false);
        }
      });
      api.draw();
      paintState();
    }

    function clearFilter(key) {
      const f = STATE[key];
      if (!f) return;
      const i = colIndex(key);
      if (i >= 0 && (f.type === 'text' || f.type === 'choice')) api.column(i).search('');
      delete STATE[key];
      api.draw();
      paintState();
    }

    function clearAll() {
      Object.keys(STATE).forEach(clearFilter);
    }

    /* ---------- the chip bar ---------- */
    function labelFor(key) {
      const th = headerFor(key);
      return (th && th.dataset.label) || key;
    }

    function summaryFor(key) {
      const f = STATE[key];
      if (f.type === 'text') return '“' + f.value + '”';
      if (f.type === 'choice') return f.value.join(', ');
      if (f.type === 'number') {
        const lo = f.value.min, hi = f.value.max;
        if (lo !== undefined && hi !== undefined) return lo + ' – ' + hi;
        if (lo !== undefined) return '≥ ' + lo;
        return '≤ ' + hi;
      }
      const v = f.value;
      if (v.mode === 'eq') return 'on ' + v.from;
      if (v.mode === 'before') return 'before ' + v.from;
      if (v.mode === 'after') return 'after ' + v.from;
      if (v.from && v.to) return v.from + ' → ' + v.to;
      if (v.from) return 'from ' + v.from;
      return 'until ' + v.to;
    }

    function paintState() {
      // The heading exists two or three times over (scroll head, scroll body,
      // and FixedHeader's floating clone), so the funnels are painted globally.
      document.querySelectorAll('.col-filter-btn').forEach(function (btn) {
        btn.classList.toggle('is-active', !!STATE[btn.dataset.colKey]);
      });
      const bar = BAR.querySelector('.tf-chips');
      bar.innerHTML = '';
      const keys = Object.keys(STATE);
      keys.forEach(function (key) {
        const chip = document.createElement('span');
        chip.className = 'fb-chip';
        chip.dataset.key = key;
        chip.appendChild(document.createTextNode(labelFor(key) + ': ' + summaryFor(key)));
        const x = document.createElement('button');
        x.type = 'button';
        x.title = 'Remove this filter';
        x.innerHTML = '<i class="material-symbols-rounded">close</i>';
        x.addEventListener('click', function () { clearFilter(key); });
        chip.appendChild(x);
        bar.appendChild(chip);
      });
      if (keys.length > 1) {
        const all = document.createElement('button');
        all.type = 'button';
        all.className = 'btn btn-link text-secondary p-0 mb-0 tf-clear-all';
        all.textContent = 'Clear all';
        all.addEventListener('click', clearAll);
        bar.appendChild(all);
      }
      paintReset();
    }

    /* ---------- popover contents ---------- */
    function distinctValues(key) {
      const i = colIndex(key);
      if (i < 0) return [];
      const seen = {};
      api.column(i).nodes().toArray().forEach(function (td) {
        const v = textOf(td);
        if (v) seen[v] = true;
      });
      return Object.keys(seen).sort();
    }

    function buildContent(th) {
      const key = th.dataset.colKey;
      const type = th.dataset.filter;
      const cur = STATE[key];
      const wrap = document.createElement('div');

      if (type === 'text') {
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'form-control form-control-sm fp-text';
        input.placeholder = 'Contains...';
        input.value = cur ? cur.value : '';
        wrap.appendChild(input);

      } else if (type === 'number') {
        [['min', 'Minimum'], ['max', 'Maximum']].forEach(function (pair) {
          const row = document.createElement('div');
          row.className = 'fp-row';
          const lbl = document.createElement('label');
          lbl.className = 'form-label';
          lbl.textContent = pair[1];
          const input = document.createElement('input');
          input.type = 'number';
          input.step = 'any';
          input.className = 'form-control form-control-sm fp-num';
          input.dataset.which = pair[0];
          input.placeholder = 'Any';
          input.value = (cur && cur.value[pair[0]] !== undefined) ? cur.value[pair[0]] : '';
          row.appendChild(lbl);
          row.appendChild(input);
          wrap.appendChild(row);
        });

      } else if (type === 'date') {
        const mode = (cur && cur.value.mode) || 'between';
        const modeLbl = document.createElement('label');
        modeLbl.className = 'form-label';
        modeLbl.textContent = 'Condition';
        const sel = document.createElement('select');
        sel.className = 'form-select form-select-sm fp-mode';
        DATE_MODES.forEach(function (m) {
          const opt = document.createElement('option');
          opt.value = m.id;
          opt.textContent = m.label;
          if (m.id === mode) opt.selected = true;
          sel.appendChild(opt);
        });
        wrap.appendChild(modeLbl);
        wrap.appendChild(sel);

        // Both inputs are always built (so a picker is attached to each once);
        // the second is only shown for "between".
        ['from', 'to'].forEach(function (which) {
          const row = document.createElement('div');
          row.className = 'fp-row fp-row-' + which;
          const lbl = document.createElement('label');
          lbl.className = 'form-label';
          const input = document.createElement('input');
          input.type = 'text';
          input.className = 'form-control form-control-sm fp-date';
          input.dataset.which = which;
          input.placeholder = 'Pick a date';
          input.readOnly = true;              // the calendar is the only way in
          input.value = cur ? (cur.value[which] || '') : '';
          row.appendChild(lbl);
          row.appendChild(input);
          wrap.appendChild(row);
        });
        const paintMode = function () {
          const m = DATE_MODES.filter(function (x) { return x.id === sel.value; })[0];
          wrap.querySelector('.fp-row-from label').textContent = m.first;
          const toRow = wrap.querySelector('.fp-row-to');
          toRow.classList.toggle('d-none', !m.second);
          if (m.second) wrap.querySelector('.fp-row-to label').textContent = m.second;
        };
        sel.addEventListener('change', paintMode);
        paintMode();

      } else if (type === 'choice') {
        const choices = (th.dataset.choices || '').split(',')
          .map(function (s) { return s.trim(); }).filter(Boolean);
        const list = choices.length ? choices : distinctValues(key);
        const box = document.createElement('div');
        box.className = 'fp-choices';
        list.forEach(function (choice, n) {
          const row = document.createElement('div');
          row.className = 'form-check';
          const cb = document.createElement('input');
          cb.className = 'form-check-input fp-choice';
          cb.type = 'checkbox';
          cb.value = choice;
          cb.id = 'fpc_' + tableId + '_' + key + '_' + n;
          cb.checked = !!(cur && cur.value.indexOf(choice) >= 0);
          const lbl = document.createElement('label');
          lbl.className = 'form-check-label';
          lbl.setAttribute('for', cb.id);
          lbl.textContent = choice;
          row.appendChild(cb);
          row.appendChild(lbl);
          box.appendChild(row);
        });
        if (!list.length) {
          const none = document.createElement('div');
          none.className = 'text-muted';
          none.textContent = 'Nothing to filter on yet.';
          box.appendChild(none);
        }
        wrap.appendChild(box);
      }

      const actions = document.createElement('div');
      actions.className = 'fp-actions';
      const clear = document.createElement('button');
      clear.type = 'button';
      clear.className = 'btn btn-sm btn-outline-secondary mb-0 fp-clear';
      clear.textContent = 'Clear';
      const apply = document.createElement('button');
      apply.type = 'button';
      apply.className = 'btn btn-sm btn-primary mb-0 fp-apply';
      apply.textContent = 'Apply';
      actions.appendChild(clear);
      actions.appendChild(apply);
      wrap.appendChild(actions);
      return wrap;
    }

    function readContent(th, pop) {
      const type = th.dataset.filter;
      if (type === 'text') {
        const v = (pop.querySelector('.fp-text').value || '').trim();
        return v ? { type: 'text', value: v } : null;
      }
      if (type === 'choice') {
        const picked = Array.prototype.map.call(
          pop.querySelectorAll('.fp-choice:checked'), function (b) { return b.value; });
        return picked.length ? { type: 'choice', value: picked } : null;
      }
      if (type === 'number') {
        const value = {};
        pop.querySelectorAll('.fp-num').forEach(function (i) {
          const raw = (i.value || '').trim();
          if (raw === '') return;
          const n = parseFloat(raw);
          if (!isNaN(n)) value[i.dataset.which] = n;
        });
        if (value.min === undefined && value.max === undefined) return null;
        // A backwards range matches nothing, which looks like a bug — swap it.
        if (value.min !== undefined && value.max !== undefined && value.min > value.max) {
          const t = value.min; value.min = value.max; value.max = t;
        }
        return { type: 'number', value: value };
      }
      const modeEl = pop.querySelector('.fp-mode');
      const mode = modeEl ? modeEl.value : 'between';
      const value = { mode: mode };
      pop.querySelectorAll('.fp-date').forEach(function (i) {
        const v = (i.value || '').trim();
        if (v) value[i.dataset.which] = v;
      });
      if (mode === 'between') {
        if (!value.from && !value.to) return null;
        if (value.from && value.to && value.from > value.to) {
          const t = value.from; value.from = value.to; value.to = t;
        }
      } else {
        if (!value.from) return null;      // the single-date conditions need one
        delete value.to;
      }
      return { type: 'date', value: value };
    }

    /* ---------- funnels ---------- */
    eachColumn(function (th) {
      if (!th || !th.dataset.filter || th.querySelector('.col-filter-btn')) return;
      const label = labelOf(th);
      th.dataset.label = label;
      th.classList.add('col-filter-th');

      const wrap = document.createElement('span');
      wrap.className = 'th-wrap';
      // The heading's existing nodes are MOVED, not replaced by their text: a
      // heading may carry markup the page depends on (golf entries tag each
      // heading with its group, and the Excel export reads that tag back).
      const text = document.createElement('span');
      text.className = 'th-label';
      while (th.firstChild) text.appendChild(th.firstChild);
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'col-filter-btn';
      btn.dataset.colKey = th.dataset.colKey;
      btn.title = 'Filter ' + label;
      btn.setAttribute('aria-label', 'Filter ' + label);
      // An inline SVG rather than a Material ligature: the ligature's text
      // becomes part of the heading's textContent and leaks into anything that
      // reads the column title.
      btn.innerHTML = FUNNEL_SVG;
      wrap.appendChild(text);
      wrap.appendChild(btn);
      th.appendChild(wrap);
    });

    function closePopover() {
      if (OPEN) { OPEN.dispose(); OPEN = null; OPEN_KEY = null; }
    }

    function openPopover(btn) {
      const key = btn.dataset.colKey;
      const th = headerFor(key);
      if (!th) return;
      const wasOpen = OPEN_KEY === key;
      closePopover();
      if (wasOpen) return;                 // a second click on the same funnel closes

      const body = buildContent(th);
      OPEN_KEY = key;
      OPEN = new bootstrap.Popover(btn, {
        container: 'body',
        placement: 'bottom',
        trigger: 'manual',
        html: true,
        sanitize: false,                   // Bootstrap's sanitiser strips <input>
        customClass: 'filter-pop' + (th.dataset.filter === 'date' ? ' filter-pop-date' : ''),
        title: 'Filter ' + (th.dataset.label || key),
        content: body,
      });
      btn.addEventListener('shown.bs.popover', function onShown() {
        btn.removeEventListener('shown.bs.popover', onShown);
        if (window.flatpickr) {
          body.querySelectorAll('.fp-date').forEach(function (i) {
            flatpickr(i, {
              dateFormat: 'Y-m-d',
              appendTo: body,              // travels and clips with the popover
              static: true,
              disableMobile: true,
            });
          });
        }
        const first = body.querySelector('.fp-text, .fp-num');
        if (first) first.focus();

        body.querySelector('.fp-apply').addEventListener('click', function () {
          const f = readContent(th, body);
          if (f) { STATE[key] = f; applyFilters(); } else { clearFilter(key); }
          closePopover();
        });
        body.querySelector('.fp-clear').addEventListener('click', function () {
          clearFilter(key);
          closePopover();
        });
        body.addEventListener('keydown', function (e) {
          if (e.key === 'Enter') { e.preventDefault(); body.querySelector('.fp-apply').click(); }
          if (e.key === 'Escape') closePopover();
        });
      });
      OPEN.show();
    }

    // The heading is also the sort control and ColReorder's drag handle, so the
    // funnel opts out of both — for every copy of the header, now or later.
    ['mousedown', 'touchstart', 'dblclick'].forEach(function (ev) {
      document.addEventListener(ev, function (e) {
        if (e.target.closest('.col-filter-btn')) e.stopPropagation();
      }, true);
    });
    document.addEventListener('click', function (e) {
      const btn = e.target.closest('.col-filter-btn');
      if (btn) {
        e.stopPropagation();
        e.preventDefault();
        openPopover(btn);
        return;
      }
      if (!e.target.closest('.filter-pop')) closePopover();
    }, true);

    /* ---------- the bar (chips + reset), injected above the table ---------- */
    const BAR = document.createElement('div');
    BAR.className = 'tf-bar';
    BAR.innerHTML = '<div class="tf-chips"></div>';
    const resetBtn = document.createElement('button');
    resetBtn.type = 'button';
    resetBtn.className = 'btn btn-link text-secondary p-0 mb-0 tf-reset d-none';
    resetBtn.innerHTML =
      '<i class="material-symbols-rounded align-middle">restart_alt</i> Reset column order';
    BAR.appendChild(resetBtn);

    const host = opts.barInto ? document.querySelector(opts.barInto) : null;
    if (host) {
      host.appendChild(BAR);
    } else {
      const wrapper = document.getElementById(tableId + '_wrapper') || table.parentNode;
      wrapper.parentNode.insertBefore(BAR, wrapper);
    }

    function paintReset() {
      if (!api.colReorder) return;
      const order = api.colReorder.order();
      const moved = order.some(function (v, i) { return v !== i; });
      resetBtn.classList.toggle('d-none', !moved);
    }
    resetBtn.addEventListener('click', function () {
      api.colReorder.reset();
      paintReset();
    });

    api.on('column-reorder', function () {
      closePopover();
      paintState();
    });
    api.on('draw', function () {
      // Ajax tables render their rows after init; the funnels have to reflect
      // whatever is filtered once the data is actually there.
      document.querySelectorAll('.col-filter-btn').forEach(function (btn) {
        btn.classList.toggle('is-active', !!STATE[btn.dataset.colKey]);
      });
    });

    // The funnels make every heading wider, and with scrollX/scrollY the
    // heading and the body are two separate tables sized at init — before these
    // buttons existed. Without a re-measure the headings drift off their own
    // columns.
    api.columns.adjust();
    paintState();
    return { clearAll: clearAll, state: STATE };
  }

  /* One global search hook for every table on the page. */
  function installHook() {
    if (installHook.done) return;
    installHook.done = true;
    DataTable.ext.search.push(function (settings, searchData, rowIdx) {
      const fn = TABLES[settings.nTable.id];
      return fn ? fn(rowIdx) : true;
    });
  }

  window.RegisterTable = {
    /* Options to merge into a DataTable config: drag-to-reorder, remembered in
       this browser. stateDuration 0 = localStorage with no expiry (-1 would be
       sessionStorage). Only the layout is restored — a filter still silently
       applied after a reload is indistinguishable from missing data. */
    options: function (o) {
      o = o || {};
      // ColReorder 2 has no fixedColumnsLeft/Right (those were 1.x); it takes a
      // `columns` selector naming which headings may be dragged. Silently
      // ignoring the old names let the checkbox column be dragged away from the
      // left edge, which breaks select-all and the export's column positions.
      const colReorder = { enable: true };
      const parts = [];
      if (o.fixedLeft) parts.push(':gt(' + (o.fixedLeft - 1) + ')');
      for (let i = 0; i < (o.fixedRight || 0); i++) {
        parts.push(':not(:nth-last-child(' + (i + 1) + '))');
      }
      if (parts.length) colReorder.columns = parts.join('');
      return {
        colReorder: colReorder,
        stateSave: true,
        stateDuration: 0,
        stateSaveParams: function (settings, data) {
          if (data.search) data.search.search = '';
          (data.columns || []).forEach(function (c) {
            if (c.search) c.search.search = '';
          });
          data.start = 0;
        },
      };
    },

    enhance: function (api, opts) {
      installHook();
      return enhance(api, opts);
    },
  };
})(window, document);
