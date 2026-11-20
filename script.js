/* ==========================================================================
   CarQuoteCheck — Client-Side US Car Dealership OTD & Junk-Fee Auditor
   Zero Frameworks | Zero Backend | 100% Private Browser Execution
   ========================================================================== */

(function () {
  'use strict';

  const STORAGE_KEY = 'carquotecheck_saved_quotes_v1';
  const MAX_SAVED_QUOTES = 4;

  let STATES = [];
  let STATES_MAP = {};
  let LAST_AUDIT = null;
  let ACTIVE_TONE = 'polite';

  // 55+ Junk Fee & Mandatory Fee Classifier Keywords
  const RED_JUNK_KEYWORDS = [
    { kw: 'vin etch', note: 'High-markup dealer profit center ($20 DIY kit). Decline or demand removal.' },
    { kw: 'etching', note: 'Window/VIN etching is optional and typically marked up 10x over cost.' },
    { kw: 'paint', note: 'Dealer paint sealants/ceramic sprays are heavily marked up. Negotiate to $0.' },
    { kw: 'fabric', note: 'Interior fabric protection is an optional add-on, not required by law.' },
    { kw: 'ceramic', note: 'Dealership ceramic coatings rarely match detail-shop quality. Decline.' },
    { kw: 'permaplate', note: 'Third-party appearance protection package. Optional and high-margin.' },
    { kw: 'cilajet', note: 'Dealer appearance sealant add-on. Optional — request removal.' },
    { kw: 'xzilon', note: 'Dealer paint/interior protection add-on. Optional and negotiable.' },
    { kw: 'resistall', note: 'Dealer protection package. You are not required to buy this.' },
    { kw: 'nitrogen', note: 'Air is already 78% nitrogen. Paying extra for nitrogen tires is a classic junk fee.' },
    { kw: 'nitro', note: 'Nitrogen tire fill is an unnecessary dealer markup.' },
    { kw: 'dealer prep', note: 'Manufacturers already reimburse dealers for Pre-Delivery Inspection (PDI).' },
    { kw: 'pdi', note: 'Pre-Delivery Inspection is covered by the automaker. Do not pay twice.' },
    { kw: 'reconditioning', note: 'Reconditioning belongs in the advertised vehicle price, not a surprise fee.' },
    { kw: 'recon', note: 'Used car reconditioning should be baked into the listed price.' },
    { kw: 'inspection', note: 'Dealer inspection fees are typically double-dipping on standard prep.' },
    { kw: 'market adjustment', note: 'Pure dealer markup above MSRP (ADM). Always negotiate or walk away.' },
    { kw: 'adm', note: 'Additional Dealer Markup (ADM) is pure profit with zero added value.' },
    { kw: 'markup', note: 'Dealer markup above MSRP is 100% negotiable.' },
    { kw: 'lojack', note: 'GPS theft tracker often pre-installed without consent. Decline activation.' },
    { kw: 'karr', note: 'KARR alarm/security systems are optional dealer profit add-ons.' },
    { kw: 'pulse', note: 'Pulsing third brake light add-on costs ~$25 wholesale. Decline.' },
    { kw: 'theft', note: 'Theft deterrent/recovery add-ons are optional and heavily marked up.' },
    { kw: 'gps', note: 'Dealer GPS tracking devices are optional. Request removal.' },
    { kw: 'tracker', note: 'Vehicle tracker add-ons are not mandatory for purchase.' },
    { kw: 'tint', note: 'Dealer window tint is often overpriced compared to local tint shops.' },
    { kw: 'wheel lock', note: 'Wheel locks cost ~$35 online; dealers often bill $150-$300.' },
    { kw: 'mud guard', note: 'Splash/mud guards are frequently bundled at inflated prices.' },
    { kw: 'splash', note: 'Dealer-installed splash guards are optional accessories.' },
    { kw: 'door edge', note: 'Door edge guards are a low-cost plastic strip sold at high markup.' },
    { kw: 'pinstripe', note: 'Dealer pinstripes are optional cosmetic markups.' },
    { kw: 'floor mat', note: 'Verify mats are not already included on the factory Monroney sticker.' },
    { kw: 'cargo', note: 'Optional dealer cargo accessory — check against factory window sticker.' },
    { kw: 'appearance', note: 'Appearance protection packages are optional high-margin add-ons.' },
    { kw: 'protection', note: 'Generic protection packages are optional dealer profit boosters.' },
    { kw: 'shield', note: 'Dealer shield/guard packages are optional add-ons.' },
    { kw: 'guard', note: 'Optional dealer guard/protection product. Request removal.' },
    { kw: 'package', note: 'Dealer-added packages (Pro Pack, Advantage Pack, etc.) are negotiable.' },
    { kw: 'pro pack', note: 'Bundled dealer accessory pack — ask to remove all non-factory items.' },
    { kw: 'advantage', note: 'Dealer Advantage/VIP packages are optional profit add-ons.' },
    { kw: 'desert', note: 'Regional protection packs (Desert/Rust/Climate) are optional.' },
    { kw: 'undercoat', note: 'Modern factory vehicles already include corrosion protection.' },
    { kw: 'rust', note: 'Dealer rustproofing is rarely needed on modern factory-coated cars.' },
    { kw: 'advertising', note: 'Dealer ad/marketing fees are business overhead, not a buyer tax.' },
    { kw: 'marketing', note: 'Marketing/ad association fees should be absorbed by the dealer.' },
    { kw: 'freight', note: 'Verify this is not duplicating the factory Destination Charge already in MSRP.' },
    { kw: 'destination', note: 'Check MSRP: factory destination is usually already inside the vehicle price.' },
    { kw: 'delivery', note: 'Dealer delivery/handling fees outside factory MSRP are junk fees.' },
    { kw: 'handling', note: 'Dealer handling fees are disguised doc/profit fees.' },
    { kw: 'electronic filing', note: 'Often inflated far above actual state e-filing cost ($15-$35). Challenge it.' },
    { kw: 'e-filing', note: 'Verify actual state electronic filing cost; dealers often pad this.' },
    { kw: 'third party tag', note: 'Private tag agency fees are frequently padded above actual DMV cost.' },
    { kw: 'key replacement', note: 'Optional F&I add-on. Can be declined or bought cheaper elsewhere.' },
    { kw: 'tire and wheel', note: 'Optional road hazard plan — high dealer margin.' },
    { kw: 'gap', note: 'GAP insurance is often 50-70% cheaper through your auto insurer or credit union.' },
    { kw: 'warranty', note: 'Extended warranties are optional and negotiable; never required for loan approval.' },
    { kw: 'service contract', note: 'Vehicle service contracts (VSC) are optional F&I products.' },
    { kw: 'maintenance', note: 'Prepaid maintenance plans are optional add-ons.' }
  ];

  const GREEN_GOV_KEYWORDS = [
    'dmv', 'title', 'registration', 'license', 'plate', 'tag fee', 'smog',
    'emission', 'tire tax', 'battery fee', 'lemon law', 'excise', 'state fee', 'gov'
  ];

  // Utility Helpers
  function fmtCurrency(num) {
    const val = Number.isFinite(num) ? num : 0;
    return val.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    });
  }

  function fmtCurrencyExact(num) {
    const val = Number.isFinite(num) ? num : 0;
    return val.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  function clampNum(val) {
    const n = parseFloat(val);
    if (!Number.isFinite(n) || n < 0) return 0;
    return n;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function showToast(msg) {
    let toast = document.getElementById('cqc-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'cqc-toast';
      toast.className = 'toast';
      toast.setAttribute('role', 'status');
      toast.setAttribute('aria-live', 'polite');
      document.body.appendChild(toast);
    }
    toast.innerHTML = '<i class="fa-solid fa-circle-check"></i> <span>' + escapeHtml(msg) + '</span>';
    toast.classList.add('is-visible');
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () {
      toast.classList.remove('is-visible');
    }, 2800);
  }

  // Safe Loan EMI Calculation (handles 0% APR without dividing by zero)
  function calcMonthlyPayment(principal, annualRatePct, months) {
    const p = Math.max(0, principal);
    const m = Math.max(1, Math.round(months));
    const r = Math.max(0, annualRatePct) / 100 / 12;
    if (p === 0) return 0;
    if (r === 0) return p / m;
    const factor = Math.pow(1 + r, m);
    return (p * r * factor) / (factor - 1);
  }

  // Classify a dealer add-on line item
  function classifyAddon(name) {
    const lower = (name || '').trim().toLowerCase();
    for (let i = 0; i < GREEN_GOV_KEYWORDS.length; i++) {
      if (lower.includes(GREEN_GOV_KEYWORDS[i])) {
        return {
          status: 'safe',
          label: 'Gov / Mandatory',
          taxable: false,
          removable: false,
          note: 'Appears to be a government or statutory fee. Verify against official state DMV schedule.'
        };
      }
    }
    for (let i = 0; i < RED_JUNK_KEYWORDS.length; i++) {
      if (lower.includes(RED_JUNK_KEYWORDS[i].kw)) {
        return {
          status: 'danger',
          label: 'Junk / Negotiable',
          taxable: true,
          removable: true,
          note: RED_JUNK_KEYWORDS[i].note
        };
      }
    }
    return {
      status: 'danger',
      label: 'Dealer Add-On',
      taxable: true,
      removable: true,
      note: 'Unverified dealer-added fee or accessory. Ask for proof it is legally required or request removal.'
    };
  }

  // =========================================================================
  // Saved Quotes (localStorage) & Comparator Modal
  // =========================================================================
  function getSavedQuotes() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      return Array.isArray(parsed) ? parsed : [];
    } catch (e) {
      return [];
    }
  }

  function setSavedQuotes(list) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    } catch (e) {
      // Ignore storage quota errors
    }
    updateSavedBadge();
  }

  function updateSavedBadge() {
    const count = getSavedQuotes().length;
    document.querySelectorAll('.js-saved-count').forEach(function (el) {
      el.textContent = String(count);
    });
  }

  function renderComparatorModal() {
    const body = document.getElementById('compare-modal-body');
    if (!body) return;
    const quotes = getSavedQuotes();
    if (quotes.length === 0) {
      body.innerHTML =
        '<div style="text-align:center;padding:28px 12px;color:var(--text-secondary);">' +
        '<i class="fa-solid fa-scale-balanced" style="font-size:2rem;color:var(--text-muted);margin-bottom:10px;display:block;"></i>' +
        '<p style="margin:0 0 6px;font-weight:600;color:var(--text-primary);">No saved dealer quotes yet</p>' +
        '<p style="margin:0;font-size:0.9rem;">Run an audit and click <strong>Save &amp; Compare Quote</strong> to compare up to 4 dealership offers side by side.</p>' +
        '</div>';
      return;
    }

    let html = '<div class="table-scroll"><table class="audit-table"><thead><tr>' +
      '<th>Label / State</th>' +
      '<th class="col-right">Vehicle Price</th>' +
      '<th class="col-right">Doc Fee</th>' +
      '<th class="col-right">Junk Add-Ons</th>' +
      '<th class="col-right">Quoted OTD</th>' +
      '<th class="col-right">Fair Target OTD</th>' +
      '<th class="col-right">Score</th>' +
      '<th>Action</th>' +
      '</tr></thead><tbody>';

    quotes.forEach(function (q, idx) {
      const scoreBadge = q.score >= 80 ? 'badge-safe' : (q.score >= 55 ? 'badge-warn' : 'badge-danger');
      html += '<tr>' +
        '<td><strong>' + escapeHtml(q.label) + '</strong><span class="fee-note">' + escapeHtml(q.stateName) + ' (' + escapeHtml(q.stateCode) + ')</span></td>' +
        '<td class="col-right">' + fmtCurrency(q.vehiclePrice) + '</td>' +
        '<td class="col-right">' + fmtCurrency(q.docFee) + '</td>' +
        '<td class="col-right">' + fmtCurrency(q.junkTotal) + '</td>' +
        '<td class="col-right"><strong>' + fmtCurrency(q.quotedOTD) + '</strong></td>' +
        '<td class="col-right" style="color:var(--safe);">' + fmtCurrency(q.fairOTD) + '</td>' +
        '<td class="col-right"><span class="badge ' + scoreBadge + '">' + q.score + '/100</span></td>' +
        '<td><button type="button" class="btn-ghost js-delete-quote" data-idx="' + idx + '" aria-label="Remove saved quote"><i class="fa-solid fa-trash-can"></i></button></td>' +
        '</tr>';
    });

    html += '</tbody></table></div>';
    body.innerHTML = html;

    body.querySelectorAll('.js-delete-quote').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const i = parseInt(btn.getAttribute('data-idx'), 10);
        const list = getSavedQuotes();
        list.splice(i, 1);
        setSavedQuotes(list);
        renderComparatorModal();
        showToast('Quote removed from comparison.');
      });
    });
  }

  function openComparatorModal() {
    const modal = document.getElementById('compare-modal');
    if (!modal) return;
    renderComparatorModal();
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
  }

  function closeComparatorModal() {
    const modal = document.getElementById('compare-modal');
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
  }

  // =========================================================================
  // Mobile Navigation & Global Listeners
  // =========================================================================
  function initNavigation() {
    const menuBtn = document.getElementById('mobile-menu-btn');
    const drawer = document.getElementById('mobile-drawer');
    if (menuBtn && drawer) {
      const closeDrawer = function () {
        drawer.classList.remove('is-open');
        menuBtn.setAttribute('aria-expanded', 'false');
        const icon = menuBtn.querySelector('i');
        if (icon) {
          icon.classList.remove('fa-xmark');
          icon.classList.add('fa-bars');
        }
      };

      menuBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        const isOpen = drawer.classList.toggle('is-open');
        menuBtn.setAttribute('aria-expanded', String(isOpen));
        const icon = menuBtn.querySelector('i');
        if (icon) {
          icon.classList.toggle('fa-bars', !isOpen);
          icon.classList.toggle('fa-xmark', isOpen);
        }
      });

      drawer.querySelectorAll('a, button').forEach(function (el) {
        el.addEventListener('click', closeDrawer);
      });

      document.addEventListener('click', function (e) {
        if (drawer.classList.contains('is-open') && !drawer.contains(e.target) && !menuBtn.contains(e.target)) {
          closeDrawer();
        }
      });

      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          closeDrawer();
          closeComparatorModal();
        }
      });
    }

    document.querySelectorAll('.js-open-compare').forEach(function (btn) {
      btn.addEventListener('click', openComparatorModal);
    });

    const modal = document.getElementById('compare-modal');
    if (modal) {
      modal.addEventListener('click', function (e) {
        if (e.target === modal) closeComparatorModal();
      });
      const closeBtn = modal.querySelector('.modal-close');
      if (closeBtn) closeBtn.addEventListener('click', closeComparatorModal);
    }

    // FAQ Accordion
    document.querySelectorAll('.faq-trigger').forEach(function (trigger) {
      trigger.addEventListener('click', function () {
        const item = trigger.closest('.faq-item');
        if (!item) return;
        const isOpen = item.classList.toggle('is-open');
        trigger.setAttribute('aria-expanded', String(isOpen));
      });
    });

    // Showroom Red-Flag Checklist
    document.querySelectorAll('.checklist-item input[type="checkbox"]').forEach(function (cb) {
      cb.addEventListener('change', function () {
        const label = cb.closest('.checklist-item');
        if (label) label.classList.toggle('is-checked', cb.checked);
      });
    });

    // Contact page copy email button
    document.querySelectorAll('.js-copy-email').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const email = btn.getAttribute('data-email') || 'hello@carquotecheck.com';
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(email).then(function () {
            showToast('Email copied: ' + email);
          });
        } else {
          showToast('Email: ' + email);
        }
      });
    });

    updateSavedBadge();
  }

  // =========================================================================
  // Instant State Search Bar & Directory Table Filter
  // =========================================================================
  function initStateSearch() {
    document.querySelectorAll('.js-state-search-input').forEach(function (input) {
      const wrap = input.closest('.state-search-wrap');
      const dropdown = wrap ? wrap.querySelector('.state-search-dropdown') : null;
      if (!dropdown) return;

      const renderMatches = function (query) {
        const q = query.trim().toLowerCase();
        if (!q) {
          dropdown.classList.remove('is-open');
          dropdown.innerHTML = '';
          return;
        }
        const matches = STATES.filter(function (s) {
          return s.name.toLowerCase().includes(q) || s.code.toLowerCase() === q || s.code.toLowerCase().startsWith(q);
        }).slice(0, 8);

        if (matches.length === 0) {
          dropdown.innerHTML = '<div class="state-search-empty">No matching US state or DC found.</div>';
        } else {
          dropdown.innerHTML = matches.map(function (s) {
            const capBadge = s.doc_fee_cap !== null
              ? '<span class="badge badge-safe">Cap: $' + s.doc_fee_cap + '</span>'
              : '<span class="badge badge-warn">Uncapped (~$' + s.avg_doc_fee + ')</span>';
            return '<a class="state-search-item" href="/' + s.slug + '/">' +
              '<span>' + escapeHtml(s.name) + ' (' + escapeHtml(s.code) + ')</span>' +
              capBadge +
              '</a>';
          }).join('');
        }
        dropdown.classList.add('is-open');
      };

      input.addEventListener('input', function () {
        renderMatches(input.value);
      });

      input.addEventListener('focus', function () {
        if (input.value.trim()) renderMatches(input.value);
      });

      document.addEventListener('click', function (e) {
        if (!wrap.contains(e.target)) {
          dropdown.classList.remove('is-open');
        }
      });
    });

    // Homepage 50-State Directory Filter
    const dirFilter = document.getElementById('directory-filter');
    const dirBody = document.getElementById('directory-table-body');
    if (dirFilter && dirBody) {
      dirFilter.addEventListener('input', function () {
        const q = dirFilter.value.trim().toLowerCase();
        dirBody.querySelectorAll('tr').forEach(function (tr) {
          const text = tr.textContent.toLowerCase();
          tr.style.display = text.includes(q) ? '' : 'none';
        });
      });
    }
  }

  // =========================================================================
  // Calculator Logic (Button-Triggered Output Only)
  // =========================================================================
  function initCalculator() {
    const form = document.getElementById('auditor-form');
    if (!form) return;

    const stateSelect = document.getElementById('state-select');
    const priceInput = document.getElementById('vehicle-price');
    const tradeInput = document.getElementById('trade-in');
    const docFeeInput = document.getElementById('doc-fee');
    const taxRateInput = document.getElementById('tax-rate');
    const titleRegInput = document.getElementById('title-reg-fee');
    const addonsList = document.getElementById('addons-list');
    const addAddonBtn = document.getElementById('btn-add-addon');
    const financeToggle = document.getElementById('finance-toggle');
    const financeFields = document.getElementById('finance-fields');
    const downPaymentInput = document.getElementById('down-payment');
    const aprInput = document.getElementById('loan-apr');
    const termInput = document.getElementById('loan-term');
    const formError = document.getElementById('form-error');
    const resultsSection = document.getElementById('audit-results');
    const alertBanner = document.getElementById('state-alert-banner');

    // Populate state dropdown
    if (stateSelect) {
      stateSelect.innerHTML = '<option value="">Select your state (50 States + DC)...</option>' +
        STATES.map(function (s) {
          const capText = s.doc_fee_cap !== null ? 'Cap $' + s.doc_fee_cap : 'Uncapped';
          return '<option value="' + s.code + '">' + escapeHtml(s.name) + ' (' + s.code + ') — ' + capText + '</option>';
        }).join('');
    }

    function updateStateContext(code, overwriteNumbers) {
      const st = STATES_MAP[code];
      document.querySelectorAll('.js-quick-state').forEach(function (chip) {
        chip.classList.toggle('is-active', chip.getAttribute('data-state') === code);
      });

      if (!st) {
        if (alertBanner) alertBanner.classList.remove('is-visible');
        return;
      }

      if (overwriteNumbers) {
        docFeeInput.value = st.avg_doc_fee;
        taxRateInput.value = st.avg_combined_tax_pct;
        titleRegInput.value = st.avg_title_reg_fee;
      }

      if (alertBanner) {
        const capBadge = st.doc_fee_cap !== null
          ? '<span class="badge badge-safe"><i class="fa-solid fa-gavel"></i> Legal Doc Cap: $' + st.doc_fee_cap + '</span>'
          : '<span class="badge badge-warn"><i class="fa-solid fa-triangle-exclamation"></i> No Doc Cap (Avg $' + st.avg_doc_fee + ')</span>';
        const tradeBadge = st.trade_in_tax_credit
          ? '<span class="badge badge-safe"><i class="fa-solid fa-check"></i> Trade-In Tax Credit: Yes</span>'
          : '<span class="badge badge-danger"><i class="fa-solid fa-xmark"></i> Trade-In Tax Credit: No</span>';
        const docTaxBadge = st.doc_fee_taxable
          ? '<span class="badge badge-neutral">Doc Fee Taxed: Yes</span>'
          : '<span class="badge badge-neutral">Doc Fee Taxed: No</span>';

        alertBanner.innerHTML =
          '<i class="fa-solid fa-circle-info"></i>' +
          '<div><strong>' + escapeHtml(st.name) + ' Rule Alert:</strong> ' + escapeHtml(st.special_alert) +
          '<div class="state-alert-meta">' + capBadge + tradeBadge + docTaxBadge + '</div></div>';
        alertBanner.classList.add('is-visible');
      }
    }

    function addAddonRow(nameVal, amountVal) {
      const row = document.createElement('div');
      row.className = 'addon-row';
      row.innerHTML =
        '<input type="text" class="form-control js-addon-name" placeholder="e.g., VIN Etching, Paint Protection" value="' + escapeHtml(nameVal || '') + '" aria-label="Dealer fee or add-on name">' +
        '<div class="input-wrap"><span class="input-prefix">$</span><input type="number" min="0" step="1" class="form-control has-prefix js-addon-amount" placeholder="0" value="' + (amountVal !== undefined && amountVal !== '' ? escapeHtml(amountVal) : '') + '" aria-label="Fee dollar amount"></div>' +
        '<button type="button" class="btn-remove-addon" aria-label="Remove fee row"><i class="fa-solid fa-trash-can"></i></button>';
      row.querySelector('.btn-remove-addon').addEventListener('click', function () {
        row.remove();
      });
      addonsList.appendChild(row);
    }

    if (stateSelect) {
      stateSelect.addEventListener('change', function () {
        updateStateContext(stateSelect.value, true);
      });
    }

    // Quick-tap state chips
    document.querySelectorAll('.js-quick-state').forEach(function (chip) {
      chip.addEventListener('click', function () {
        const code = chip.getAttribute('data-state');
        if (stateSelect && STATES_MAP[code]) {
          stateSelect.value = code;
          updateStateContext(code, true);
        }
      });
    });

    // Add-on button & quick-tap junk chips
    if (addAddonBtn) {
      addAddonBtn.addEventListener('click', function () {
        addAddonRow('', '');
      });
    }

    document.querySelectorAll('.js-quick-addon').forEach(function (chip) {
      chip.addEventListener('click', function () {
        const label = chip.getAttribute('data-addon');
        const defaultAmt = chip.getAttribute('data-amount') || '';
        addAddonRow(label, defaultAmt);
      });
    });

    // Financing toggle
    if (financeToggle && financeFields) {
      financeToggle.addEventListener('change', function () {
        financeFields.classList.toggle('is-visible', financeToggle.checked);
      });
    }

    // Try Sample Quote Button
    const sampleBtn = document.getElementById('btn-sample-quote');
    if (sampleBtn) {
      sampleBtn.addEventListener('click', function () {
        const currentDefault = document.body.dataset.defaultState || '';
        const targetState = stateSelect.value || currentDefault || 'FL';
        stateSelect.value = targetState;
        updateStateContext(targetState, true);
        const st = STATES_MAP[targetState];
        priceInput.value = '34500';
        tradeInput.value = '8000';
        docFeeInput.value = st && st.doc_fee_cap !== null ? String(st.doc_fee_cap + 250) : '995';
        addonsList.innerHTML = '';
        addAddonRow('VIN Etching', '399');
        addAddonRow('Paint & Fabric Protection', '895');
        addAddonRow('Nitrogen Tires', '199');
        financeToggle.checked = true;
        financeFields.classList.add('is-visible');
        downPaymentInput.value = '3000';
        aprInput.value = '6.9';
        termInput.value = '60';
        runAudit(true);
      });
    }

    // Reset Button
    const resetBtn = document.getElementById('btn-reset-quote');
    if (resetBtn) {
      resetBtn.addEventListener('click', function () {
        const defaultSt = document.body.dataset.defaultState || '';
        stateSelect.value = defaultSt;
        priceInput.value = '';
        tradeInput.value = '';
        addonsList.innerHTML = '';
        financeToggle.checked = false;
        financeFields.classList.remove('is-visible');
        downPaymentInput.value = '0';
        aprInput.value = '6.5';
        termInput.value = '60';
        if (defaultSt) {
          updateStateContext(defaultSt, true);
        } else {
          docFeeInput.value = '';
          taxRateInput.value = '';
          titleRegInput.value = '';
          if (alertBanner) alertBanner.classList.remove('is-visible');
        }
        if (formError) formError.classList.remove('is-visible');
        if (resultsSection) resultsSection.classList.remove('is-visible');
        priceInput.classList.remove('is-invalid');
        stateSelect.classList.remove('is-invalid');
        LAST_AUDIT = null;
      });
    }

    // Generate Counter-Offer Email Text (3 Tones)
    function buildEmailText(audit, tone) {
      const capLine = audit.state.doc_fee_cap !== null
        ? 'In ' + audit.state.name + ', the statutory dealer doc fee cap is ' + fmtCurrency(audit.state.doc_fee_cap) + '.'
        : 'While ' + audit.state.name + ' does not cap doc fees, ' + fmtCurrency(audit.docFee) + ' is well above a fair processing cost.';

      const junkNames = audit.addons
        .filter(function (a) { return a.removable && a.amount > 0; })
        .map(function (a) { return a.name + ' (' + fmtCurrency(a.amount) + ')'; });

      const removeStr = junkNames.length > 0
        ? 'removing the optional dealer add-ons (' + junkNames.join(', ') + ')'
        : 'adjusting the dealership fee structure';

      if (tone === 'polite') {
        return 'Subject: Out-the-Door Price Inquiry — Ready to Purchase\n\n' +
          'Hi [Salesperson Name],\n\n' +
          'Thank you for sending over the quote at ' + fmtCurrency(audit.quotedOTD) + ' out-the-door. I am very interested in moving forward with this vehicle.\n\n' +
          'After reviewing the line-item breakdown for ' + audit.state.name + ', I would like to request ' + removeStr + '. ' + capLine + '\n\n' +
          'If we can agree on a clean Out-the-Door total of ' + fmtCurrency(audit.fairOTD) + ' (including vehicle price, ' + audit.state.name + ' taxes, and official title/registration), I am ready to finalize the deal this week.\n\n' +
          'Please let me know if you can send an updated itemized buyer\'s order.\n\n' +
          'Best regards,\n[Your Name]';
      }

      if (tone === 'firm') {
        return 'Subject: Counter-Offer: ' + fmtCurrency(audit.fairOTD) + ' Out-the-Door\n\n' +
          'Hi [Salesperson Name],\n\n' +
          'I audited the buyer\'s order you provided (' + fmtCurrency(audit.quotedOTD) + ' OTD). There is ' + fmtCurrency(audit.potentialSavings) + ' in non-mandatory dealer fees and markups that I will not pay.\n\n' +
          'Specifically, I am declining ' + removeStr + '. ' + capLine + '\n\n' +
          'My firm Out-the-Door offer is ' + fmtCurrency(audit.fairOTD) + ' total — vehicle price plus legitimate state taxes and DMV fees only. If your manager approves this OTD figure, send the revised sheet and I will come in to sign.\n\n' +
          'Thanks,\n[Your Name]';
      }

      return 'Subject: Final OTD Offer — ' + fmtCurrency(audit.fairOTD) + '\n\n' +
        'Hi [Salesperson Name],\n\n' +
        'I am comparing OTD quotes from three dealerships today. Your current quote of ' + fmtCurrency(audit.quotedOTD) + ' includes ' + fmtCurrency(audit.potentialSavings) + ' in unnecessary dealer fees/add-ons.\n\n' +
        capLine + ' I am only willing to purchase at ' + fmtCurrency(audit.fairOTD) + ' Out-the-Door with zero dealer add-ons.\n\n' +
        'If you can match ' + fmtCurrency(audit.fairOTD) + ' OTD, let me know by end of day; otherwise I will move forward with another dealer.\n\n' +
        'Regards,\n[Your Name]';
    }

    // Core Audit Computation & Render
    function runAudit(shouldScroll) {
      const code = stateSelect.value;
      const st = STATES_MAP[code];
      const vehiclePrice = clampNum(priceInput.value);

      stateSelect.classList.remove('is-invalid');
      priceInput.classList.remove('is-invalid');
      if (formError) formError.classList.remove('is-visible');

      if (!st) {
        stateSelect.classList.add('is-invalid');
        if (formError) {
          formError.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Please select a US state or Washington, DC to apply local doc fee and tax rules.';
          formError.classList.add('is-visible');
        }
        stateSelect.focus();
        return;
      }

      if (vehiclePrice <= 0) {
        priceInput.classList.add('is-invalid');
        if (formError) {
          formError.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Please enter a valid Vehicle Selling Price greater than $0.';
          formError.classList.add('is-visible');
        }
        priceInput.focus();
        return;
      }

      // Clamp all inputs cleanly
      const tradeIn = clampNum(tradeInput.value);
      const docFee = clampNum(docFeeInput.value);
      const taxRate = clampNum(taxRateInput.value);
      const titleReg = clampNum(titleRegInput.value);

      // Collect dynamic add-ons
      const addons = [];
      let taxableAddonsTotal = 0;
      let nonTaxableAddonsTotal = 0;
      let removableAddonsTotal = 0;
      let removableTaxableAddons = 0;

      addonsList.querySelectorAll('.addon-row').forEach(function (row) {
        const name = (row.querySelector('.js-addon-name').value || '').trim();
        const amount = clampNum(row.querySelector('.js-addon-amount').value);
        if (!name && amount === 0) return;
        const label = name || 'Unnamed Dealer Fee';
        const info = classifyAddon(label);
        addons.push({
          name: label,
          amount: amount,
          status: info.status,
          label: info.label,
          taxable: info.taxable,
          removable: info.removable,
          note: info.note
        });
        if (info.taxable) taxableAddonsTotal += amount;
        else nonTaxableAddonsTotal += amount;
        if (info.removable) {
          removableAddonsTotal += amount;
          if (info.taxable) removableTaxableAddons += amount;
        }
      });

      // Evaluate Doc Fee Status & Fair Doc Fee Benchmark
      let docStatus = 'safe';
      let docBadgeLabel = 'Fair Doc Fee';
      let docNote = 'Within normal range for ' + st.name + '.';
      let fairDocFee = docFee;

      if (st.doc_fee_cap !== null) {
        if (docFee > st.doc_fee_cap) {
          docStatus = 'danger';
          docBadgeLabel = 'Exceeds Legal Cap';
          docNote = st.name + ' legally caps doc fees at ' + fmtCurrency(st.doc_fee_cap) + '. You are being overcharged by ' + fmtCurrency(docFee - st.doc_fee_cap) + '.';
          fairDocFee = st.doc_fee_cap;
        } else {
          docStatus = 'safe';
          docBadgeLabel = 'Within Legal Cap';
          docNote = 'Compliant with ' + st.name + ' statutory cap of ' + fmtCurrency(st.doc_fee_cap) + '.';
        }
      } else {
        if (docFee > 500) {
          docStatus = 'warn';
          docBadgeLabel = 'High Uncapped Fee';
          docNote = st.name + ' has no doc fee cap (avg ' + fmtCurrency(st.avg_doc_fee) + '). Negotiate vehicle price down to offset fees above $400.';
          fairDocFee = Math.min(docFee, 400);
        } else if (docFee > 250) {
          docStatus = 'warn';
          docBadgeLabel = 'Uncapped State';
          docNote = 'Reasonable for an uncapped state, though still pure dealer margin.';
        }
      }

      // Accurate US Tax Calculation (Never Negative; Gov Title/Reg Excluded)
      const tradeCreditAmt = st.trade_in_tax_credit ? tradeIn : 0;
      const quotedTaxableBase = Math.max(0, vehiclePrice - tradeCreditAmt + (st.doc_fee_taxable ? docFee : 0) + taxableAddonsTotal);
      let quotedTax = quotedTaxableBase * (taxRate / 100);
      let taxNote = 'Calculated on ' + fmtCurrency(quotedTaxableBase) + ' taxable base' +
        (st.trade_in_tax_credit && tradeIn > 0 ? ' (after trade-in credit)' : '') +
        (st.doc_fee_taxable ? ' including doc fee.' : ' excluding doc fee.');

      // South Carolina $500 max Infrastructure Maintenance Fee cap
      if (st.code === 'SC' && quotedTax > 500) {
        quotedTax = 500;
        taxNote = 'South Carolina caps its 5% Infrastructure Maintenance Fee at a flat $500 maximum per vehicle.';
      }

      const fairTaxableBase = Math.max(0, vehiclePrice - tradeCreditAmt + (st.doc_fee_taxable ? fairDocFee : 0) + (taxableAddonsTotal - removableTaxableAddons));
      let fairTax = fairTaxableBase * (taxRate / 100);
      if (st.code === 'SC' && fairTax > 500) fairTax = 500;

      // Out-The-Door Totals (before trade-in equity subtraction? Standard OTD = Price + Fees + Tax; show net after trade-in if tradeIn > 0)
      const quotedOTD = vehiclePrice + docFee + taxableAddonsTotal + nonTaxableAddonsTotal + quotedTax + titleReg;
      const fairOTD = vehiclePrice + fairDocFee + (taxableAddonsTotal - removableTaxableAddons) + nonTaxableAddonsTotal + fairTax + titleReg;
      const potentialSavings = Math.max(0, quotedOTD - fairOTD);
      const excessDocFee = Math.max(0, docFee - fairDocFee);

      // Deal Fairness Score (0-100)
      let score = 100;
      if (st.doc_fee_cap !== null && docFee > st.doc_fee_cap) {
        score -= 25;
      } else if (docFee > 799) {
        score -= 18;
      } else if (docFee > 500) {
        score -= 10;
      }
      const junkRatio = vehiclePrice > 0 ? (removableAddonsTotal / vehiclePrice) : 0;
      score -= Math.min(45, Math.round(junkRatio * 450));
      score -= Math.min(20, addons.filter(function (a) { return a.removable && a.amount > 0; }).length * 6);
      score = Math.max(12, Math.min(100, score));

      let scoreVerdict = 'Clean & Fair Quote';
      let scoreColor = 'var(--safe)';
      if (score < 55) {
        scoreVerdict = 'Heavy Junk-Fee Markup';
        scoreColor = 'var(--danger)';
      } else if (score < 80) {
        scoreVerdict = 'Negotiable Fees Detected';
        scoreColor = 'var(--warn)';
      }

      // Financing / Hidden Loan Trap Calculation
      const isFinancing = financeToggle && financeToggle.checked;
      let loanData = null;
      if (isFinancing) {
        const downPay = clampNum(downPaymentInput.value);
        const apr = clampNum(aprInput.value);
        const term = Math.max(12, Math.round(clampNum(termInput.value) || 60));

        const quotedPrincipal = Math.max(0, quotedOTD - tradeIn - downPay);
        const fairPrincipal = Math.max(0, fairOTD - tradeIn - downPay);

        const quotedMonthly = calcMonthlyPayment(quotedPrincipal, apr, term);
        const fairMonthly = calcMonthlyPayment(fairPrincipal, apr, term);
        const monthlyDiff = Math.max(0, quotedMonthly - fairMonthly);

        const quotedTotalPaid = quotedMonthly * term;
        const fairTotalPaid = fairMonthly * term;
        const totalDiffWithInterest = Math.max(0, quotedTotalPaid - fairTotalPaid);
        const extraInterestOnJunk = Math.max(0, totalDiffWithInterest - Math.max(0, quotedPrincipal - fairPrincipal));

        loanData = {
          apr: apr,
          term: term,
          quotedPrincipal: quotedPrincipal,
          quotedMonthly: quotedMonthly,
          fairMonthly: fairMonthly,
          monthlyDiff: monthlyDiff,
          extraInterestOnJunk: extraInterestOnJunk,
          totalJunkCostFinanced: totalDiffWithInterest
        };
      }

      LAST_AUDIT = {
        state: st,
        vehiclePrice: vehiclePrice,
        tradeIn: tradeIn,
        docFee: docFee,
        fairDocFee: fairDocFee,
        excessDocFee: excessDocFee,
        taxRate: taxRate,
        quotedTax: quotedTax,
        fairTax: fairTax,
        titleReg: titleReg,
        addons: addons,
        junkTotal: removableAddonsTotal,
        quotedOTD: quotedOTD,
        fairOTD: fairOTD,
        potentialSavings: potentialSavings,
        score: score,
        scoreVerdict: scoreVerdict,
        scoreColor: scoreColor,
        loanData: loanData
      };

      // Render Results Dashboard
      document.getElementById('res-score-val').textContent = score + ' / 100';
      document.getElementById('res-score-val').style.color = scoreColor;
      document.getElementById('res-score-verdict').textContent = scoreVerdict;
      const barFill = document.getElementById('res-score-bar');
      barFill.style.width = score + '%';
      barFill.style.background = scoreColor;

      document.getElementById('res-quoted-otd').textContent = fmtCurrency(quotedOTD);
      document.getElementById('res-quoted-sub').textContent = tradeIn > 0
        ? 'Net after ' + fmtCurrency(tradeIn) + ' trade-in: ' + fmtCurrency(Math.max(0, quotedOTD - tradeIn))
        : 'Includes taxes, doc fee, title/reg & add-ons';

      document.getElementById('res-fair-otd').textContent = fmtCurrency(fairOTD);
      document.getElementById('res-fair-sub').textContent = 'Target counter-offer for ' + st.name;

      // Savings Banner
      const savBanner = document.getElementById('res-savings-banner');
      if (potentialSavings > 0) {
        savBanner.className = 'savings-banner has-savings';
        savBanner.innerHTML =
          '<div><h3 class="savings-title" style="color:#B91C1C;"><i class="fa-solid fa-triangle-exclamation"></i> Potential Junk &amp; Excess Fee Savings Found</h3>' +
          '<p class="savings-desc">Stripping optional dealer add-ons and excess doc fees (plus tax on those fees) lowers your OTD price immediately.</p></div>' +
          '<div class="savings-amount" style="color:#B91C1C;">Save ' + fmtCurrency(potentialSavings) + '</div>';
      } else {
        savBanner.className = 'savings-banner is-clean';
        savBanner.innerHTML =
          '<div><h3 class="savings-title" style="color:#047857;"><i class="fa-solid fa-circle-check"></i> Clean Quote — No Junk Fees Flagged</h3>' +
          '<p class="savings-desc">Your quote matches ' + escapeHtml(st.name) + ' guidelines with zero suspicious dealer add-ons detected.</p></div>' +
          '<div class="savings-amount" style="color:#047857;">Fair Deal</div>';
      }

      // Line-by-Line Breakdown Table
      const tbody = document.getElementById('res-breakdown-body');
      const rows = [];

      rows.push(
        '<tr><td><strong>Vehicle Selling Price</strong><span class="fee-note">Agreed vehicle price before taxes and fees.</span></td>' +
        '<td><span class="badge badge-neutral">Base Price</span></td>' +
        '<td class="col-right">' + fmtCurrency(vehiclePrice) + '</td></tr>'
      );

      const docBadgeClass = docStatus === 'safe' ? 'badge-safe' : (docStatus === 'warn' ? 'badge-warn' : 'badge-danger');
      rows.push(
        '<tr><td><strong>Dealer Documentation Fee</strong><span class="fee-note">' + escapeHtml(docNote) + '</span></td>' +
        '<td><span class="badge ' + docBadgeClass + '">' + escapeHtml(docBadgeLabel) + '</span></td>' +
        '<td class="col-right">' + fmtCurrency(docFee) + '</td></tr>'
      );

      addons.forEach(function (a) {
        const bClass = a.status === 'safe' ? 'badge-safe' : 'badge-danger';
        rows.push(
          '<tr><td><strong>' + escapeHtml(a.name) + '</strong><span class="fee-note">' + escapeHtml(a.note) + '</span></td>' +
          '<td><span class="badge ' + bClass + '">' + escapeHtml(a.label) + '</span></td>' +
          '<td class="col-right">' + fmtCurrency(a.amount) + '</td></tr>'
        );
      });

      rows.push(
        '<tr><td><strong>Estimated Sales / Excise Tax (' + taxRate.toFixed(2) + '%)</strong><span class="fee-note">' + escapeHtml(taxNote) + '</span></td>' +
        '<td><span class="badge badge-safe">Mandatory Gov</span></td>' +
        '<td class="col-right">' + fmtCurrency(quotedTax) + '</td></tr>'
      );

      rows.push(
        '<tr><td><strong>Title, License &amp; Registration</strong><span class="fee-note">Official state DMV title/plate fees (exempt from sales tax).</span></td>' +
        '<td><span class="badge badge-safe">Mandatory Gov</span></td>' +
        '<td class="col-right">' + fmtCurrency(titleReg) + '</td></tr>'
      );

      tbody.innerHTML = rows.join('');

      // Hidden Loan Trap Box
      const loanBox = document.getElementById('res-loan-trap');
      if (loanData) {
        loanBox.classList.add('is-visible');
        document.getElementById('loan-quoted-mo').textContent = fmtCurrencyExact(loanData.quotedMonthly) + '/mo';
        document.getElementById('loan-fair-mo').textContent = fmtCurrencyExact(loanData.fairMonthly) + '/mo';
        document.getElementById('loan-extra-int').textContent = fmtCurrency(loanData.extraInterestOnJunk);
        document.getElementById('loan-total-trap').textContent = fmtCurrency(loanData.totalJunkCostFinanced);
      } else {
        loanBox.classList.remove('is-visible');
      }

      // Counter-Offer Email
      const emailArea = document.getElementById('counter-email-text');
      if (emailArea) {
        emailArea.value = buildEmailText(LAST_AUDIT, ACTIVE_TONE);
      }

      // Reveal Results Dashboard
      resultsSection.classList.add('is-visible');
      if (shouldScroll) {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }

    // Submit Handler (Button-Triggered)
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      runAudit(true);
    });

    // Tone Tabs for Counter-Offer Email
    document.querySelectorAll('.js-tone-tab').forEach(function (tab) {
      tab.addEventListener('click', function () {
        ACTIVE_TONE = tab.getAttribute('data-tone') || 'polite';
        document.querySelectorAll('.js-tone-tab').forEach(function (t) {
          t.classList.toggle('is-active', t === tab);
        });
        const emailArea = document.getElementById('counter-email-text');
        if (emailArea && LAST_AUDIT) {
          emailArea.value = buildEmailText(LAST_AUDIT, ACTIVE_TONE);
        }
      });
    });

    // Copy Counter-Offer Email
    const copyEmailBtn = document.getElementById('btn-copy-email');
    if (copyEmailBtn) {
      copyEmailBtn.addEventListener('click', function () {
        const emailArea = document.getElementById('counter-email-text');
        if (!emailArea) return;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(emailArea.value).then(function () {
            showToast('Counter-offer email copied to clipboard.');
          });
        } else {
          emailArea.select();
          document.execCommand('copy');
          showToast('Counter-offer email copied.');
        }
      });
    }

    // Copy Shareable Audit URL
    const shareLinkBtn = document.getElementById('btn-share-link');
    if (shareLinkBtn) {
      shareLinkBtn.addEventListener('click', function () {
        if (!LAST_AUDIT) return;
        const params = new URLSearchParams();
        params.set('state', LAST_AUDIT.state.code);
        params.set('price', String(LAST_AUDIT.vehiclePrice));
        if (LAST_AUDIT.tradeIn > 0) params.set('trade', String(LAST_AUDIT.tradeIn));
        params.set('doc', String(LAST_AUDIT.docFee));
        params.set('tax', String(LAST_AUDIT.taxRate));
        params.set('reg', String(LAST_AUDIT.titleReg));
        if (LAST_AUDIT.addons.length > 0) {
          const encodedAddons = LAST_AUDIT.addons
            .map(function (a) { return encodeURIComponent(a.name) + ':' + a.amount; })
            .join('|');
          params.set('addons', encodedAddons);
        }
        if (LAST_AUDIT.loanData) {
          params.set('fin', '1');
          params.set('down', String(clampNum(downPaymentInput.value)));
          params.set('apr', String(LAST_AUDIT.loanData.apr));
          params.set('term', String(LAST_AUDIT.loanData.term));
        }
        const url = window.location.origin + window.location.pathname + '?' + params.toString();
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(function () {
            showToast('Shareable audit link copied.');
          });
        } else {
          showToast('Link ready in address bar.');
        }
      });
    }

    // Save & Compare Quote
    const saveQuoteBtn = document.getElementById('btn-save-quote');
    if (saveQuoteBtn) {
      saveQuoteBtn.addEventListener('click', function () {
        if (!LAST_AUDIT) return;
        const list = getSavedQuotes();
        if (list.length >= MAX_SAVED_QUOTES) {
          showToast('Max 4 quotes saved. Delete one in Saved Quotes to add another.');
          openComparatorModal();
          return;
        }
        list.push({
          label: 'Dealer Quote #' + (list.length + 1),
          stateCode: LAST_AUDIT.state.code,
          stateName: LAST_AUDIT.state.name,
          vehiclePrice: LAST_AUDIT.vehiclePrice,
          docFee: LAST_AUDIT.docFee,
          junkTotal: LAST_AUDIT.junkTotal,
          quotedOTD: LAST_AUDIT.quotedOTD,
          fairOTD: LAST_AUDIT.fairOTD,
          score: LAST_AUDIT.score
        });
        setSavedQuotes(list);
        showToast('Quote saved! Click Saved Quotes to compare side by side.');
      });
    }

    // Print 1-Page Showroom Sheet
    const printBtn = document.getElementById('btn-print-sheet');
    if (printBtn) {
      printBtn.addEventListener('click', function () {
        window.print();
      });
    }

    // Download Shareable Reddit Audit Card PNG (HTML5 Canvas)
    const pngBtn = document.getElementById('btn-download-png');
    if (pngBtn) {
      pngBtn.addEventListener('click', function () {
        if (!LAST_AUDIT) return;
        const a = LAST_AUDIT;
        const canvas = document.createElement('canvas');
        canvas.width = 1080;
        canvas.height = 680;
        const ctx = canvas.getContext('2d');

        // Background
        ctx.fillStyle = '#F9FAFB';
        ctx.fillRect(0, 0, 1080, 680);

        // Top Accent Bar
        ctx.fillStyle = '#F38020';
        ctx.fillRect(0, 0, 1080, 10);

        // Card Surface
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(44, 42, 992, 596);
        ctx.strokeStyle = '#E5E7EB';
        ctx.lineWidth = 2;
        ctx.strokeRect(44, 42, 992, 596);

        // Header
        ctx.fillStyle = '#111827';
        ctx.font = 'bold 34px sans-serif';
        ctx.fillText('CarQuoteCheck  |  OTD Deal Audit', 80, 104);

        ctx.fillStyle = '#4B5563';
        ctx.font = '600 20px sans-serif';
        ctx.fillText('State: ' + a.state.name + ' (' + a.state.code + ')  •  Anonymized Showroom Summary', 80, 138);

        // 3 Metric Boxes
        const boxes = [
          { title: 'DEAL FAIRNESS SCORE', val: a.score + ' / 100', sub: a.scoreVerdict, color: a.score >= 80 ? '#10B981' : (a.score >= 55 ? '#F59E0B' : '#EF4444') },
          { title: 'QUOTED OTD PRICE', val: fmtCurrency(a.quotedOTD), sub: 'Dealer Buyer\'s Order', color: '#111827' },
          { title: 'FAIR TARGET OTD', val: fmtCurrency(a.fairOTD), sub: 'Save ' + fmtCurrency(a.potentialSavings), color: '#10B981' }
        ];
        boxes.forEach(function (b, idx) {
          const x = 80 + idx * 314;
          ctx.fillStyle = '#F9FAFB';
          ctx.fillRect(x, 170, 294, 132);
          ctx.strokeStyle = '#E5E7EB';
          ctx.strokeRect(x, 170, 294, 132);

          ctx.fillStyle = '#6B7280';
          ctx.font = 'bold 14px sans-serif';
          ctx.fillText(b.title, x + 20, 202);

          ctx.fillStyle = b.color;
          ctx.font = 'bold 36px sans-serif';
          ctx.fillText(b.val, x + 20, 250);

          ctx.fillStyle = '#4B5563';
          ctx.font = '600 16px sans-serif';
          ctx.fillText(b.sub, x + 20, 282);
        });

        // Key Line Items
        ctx.fillStyle = '#111827';
        ctx.font = 'bold 22px sans-serif';
        ctx.fillText('Audited Breakdown', 80, 350);

        const lines = [
          ['Vehicle Selling Price', fmtCurrency(a.vehiclePrice), '#111827'],
          ['Dealer Doc Fee (' + (a.state.doc_fee_cap !== null ? 'Cap $' + a.state.doc_fee_cap : 'Uncapped') + ')', fmtCurrency(a.docFee), a.excessDocFee > 0 ? '#EF4444' : '#111827'],
          ['Dealer Add-Ons / Junk Fees (' + a.addons.length + ' items)', fmtCurrency(a.junkTotal), a.junkTotal > 0 ? '#EF4444' : '#10B981'],
          ['Estimated Tax (' + a.taxRate.toFixed(2) + '%) + Title/Reg', fmtCurrency(a.quotedTax + a.titleReg), '#111827']
        ];

        lines.forEach(function (ln, idx) {
          const y = 392 + idx * 44;
          ctx.fillStyle = '#4B5563';
          ctx.font = '500 20px sans-serif';
          ctx.fillText(ln[0], 80, y);
          ctx.fillStyle = ln[2];
          ctx.font = 'bold 22px sans-serif';
          ctx.textAlign = 'right';
          ctx.fillText(ln[1], 1000, y);
          ctx.textAlign = 'left';
          ctx.strokeStyle = '#F3F4F6';
          ctx.beginPath();
          ctx.moveTo(80, y + 14);
          ctx.lineTo(1000, y + 14);
          ctx.stroke();
        });

        // Watermark Footer
        ctx.fillStyle = '#9CA3AF';
        ctx.font = '600 16px sans-serif';
        ctx.fillText('Audited privately with CarQuoteCheck  •  carquotecheck.pages.dev', 80, 608);

        const link = document.createElement('a');
        link.download = 'carquotecheck-audit-' + a.state.code.toLowerCase() + '.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
        showToast('Audit Card PNG downloaded.');
      });
    }

    // Initialize state pre-selection or URL query params
    const urlParams = new URLSearchParams(window.location.search);
    const paramState = (urlParams.get('state') || '').toUpperCase();
    const paramPrice = urlParams.get('price');

    if (paramState && STATES_MAP[paramState] && paramPrice) {
      stateSelect.value = paramState;
      updateStateContext(paramState, true);
      priceInput.value = paramPrice;
      if (urlParams.get('trade')) tradeInput.value = urlParams.get('trade');
      if (urlParams.get('doc')) docFeeInput.value = urlParams.get('doc');
      if (urlParams.get('tax')) taxRateInput.value = urlParams.get('tax');
      if (urlParams.get('reg')) titleRegInput.value = urlParams.get('reg');

      const addonsParam = urlParams.get('addons');
      if (addonsParam) {
        addonsList.innerHTML = '';
        addonsParam.split('|').forEach(function (pair) {
          const parts = pair.split(':');
          if (parts.length >= 2) {
            const amt = parts.pop();
            const nm = decodeURIComponent(parts.join(':'));
            addAddonRow(nm, amt);
          }
        });
      }

      if (urlParams.get('fin') === '1') {
        financeToggle.checked = true;
        financeFields.classList.add('is-visible');
        if (urlParams.get('down')) downPaymentInput.value = urlParams.get('down');
        if (urlParams.get('apr')) aprInput.value = urlParams.get('apr');
        if (urlParams.get('term')) termInput.value = urlParams.get('term');
      }

      runAudit(false);
    } else {
      const defaultState = (document.body.dataset.defaultState || '').toUpperCase();
      if (defaultState && STATES_MAP[defaultState]) {
        stateSelect.value = defaultState;
        updateStateContext(defaultState, true);
      }
    }
  }

  // Bootstrap App
  document.addEventListener('DOMContentLoaded', function () {
    initNavigation();
    fetch('/data/states.json')
      .then(function (res) {
        if (!res.ok) throw new Error('Failed to load states.json');
        return res.json();
      })
      .then(function (data) {
        STATES = data;
        STATES.forEach(function (s) {
          STATES_MAP[s.code] = s;
        });
        initStateSearch();
        initCalculator();
      })
      .catch(function (err) {
        console.error('CarQuoteCheck data load error:', err);
      });
  });
})();
