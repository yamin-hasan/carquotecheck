#!/usr/bin/env python3
"""
CarQuoteCheck Static Site Generator (build.py)
Generates all 57 HTML pages (Homepage, 51 State SEO Pages, 4 Legal/Trust Pages, 404),
favicon.svg, og-image.png, _headers, robots.txt, sitemap.xml, and llms.txt.

To migrate domains (e.g. to https://carquotecheck.com):
1. Update SITE_URL below.
2. Run: python3 build.py
"""

import os
import json
import html
from pathlib import Path
from urllib.parse import quote

# =============================================================================
# CONFIGURATION — Change SITE_URL and re-run `python3 build.py` to migrate!
# =============================================================================
SITE_URL = "https://carquotecheck.pages.dev"
SITE_NAME = "CarQuoteCheck"
CONTACT_EMAIL = "hello@carquotecheck.com"
BASE_DIR = Path(__file__).resolve().parent


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(rel_path: str, content: str) -> None:
    full_path = BASE_DIR / rel_path
    ensure_dir(full_path.parent)
    full_path.write_text(content, encoding="utf-8")


def fmt_cap_badge(st: dict) -> str:
    if st["doc_fee_cap"] is not None:
        return f'<span class="badge badge-safe">Cap: ${st["doc_fee_cap"]}</span>'
    return f'<span class="badge badge-warn">Uncapped (~${st["avg_doc_fee"]})</span>'


def generate_favicon() -> None:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64">
  <rect width="64" height="64" rx="14" fill="#111827"/>
  <path d="M32 10L50 18V33C50 44.5 42.2 52.8 32 56C21.8 52.8 14 44.5 14 33V18L32 10Z" fill="#F38020"/>
  <path d="M25.5 33.5L30.2 38.2L40.5 26.8" fill="none" stroke="#FFFFFF" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""
    write_text("favicon.svg", svg)


def generate_og_image() -> None:
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1200, 630
    img = Image.new("RGB", (width, height), "#F9FAFB")
    draw = ImageDraw.Draw(img)

    # Top Cloudflare Orange Accent Bar
    draw.rectangle([0, 0, width, 14], fill="#F38020")

    # Main Elevated Card
    draw.rounded_rectangle([64, 62, 1136, 568], radius=24, fill="#FFFFFF", outline="#E5E7EB", width=2)

    def load_font(size: int, bold: bool = False):
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        for path in candidates:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    f_brand = load_font(38, bold=True)
    f_h1 = load_font(54, bold=True)
    f_sub = load_font(25, bold=False)
    f_pill = load_font(18, bold=True)
    f_stat_lbl = load_font(15, bold=True)
    f_stat_val = load_font(27, bold=True)

    # Shield Icon Box
    draw.rounded_rectangle([110, 108, 162, 160], radius=12, fill="#111827")
    draw.polygon([(136, 118), (152, 125), (152, 138), (136, 150), (120, 138), (120, 125)], fill="#F38020")

    # Brand Name
    draw.text((180, 113), "CarQuote", fill="#111827", font=f_brand)
    w_cq = draw.textlength("CarQuote", font=f_brand)
    draw.text((180 + w_cq, 113), "Check", fill="#F38020", font=f_brand)

    # Trust Pill (perfectly centered)
    pill_text = "All 50 States + DC  |  100% Free"
    pill_w = draw.textlength(pill_text, font=f_pill)
    pill_x1 = 1090
    pill_x0 = pill_x1 - pill_w - 44
    draw.rounded_rectangle([pill_x0, 112, pill_x1, 156], radius=22, fill="#FFF7ED", outline="#FED7AA", width=2)
    draw.text((pill_x0 + 22, 123), pill_text, fill="#EA580C", font=f_pill)

    # Headline
    draw.text((110, 206), "Audit Your Car Dealership", fill="#111827", font=f_h1)
    draw.text((110, 272), "OTD Quote & Junk Fees", fill="#F38020", font=f_h1)

    # Subtitle
    draw.text((110, 352), "Instant state doc fee cap checks, sales tax math & counter-offer scripts.", fill="#4B5563", font=f_sub)

    # 3 Mini Feature Cards at Bottom
    cards = [
        ("DOC FEE CAPS", "50 States + DC", "#10B981"),
        ("JUNK FEE RADAR", "55+ Red Flags", "#EF4444"),
        ("PRIVACY FIRST", "100% In-Browser", "#F38020"),
    ]
    for idx, (lbl, val, col) in enumerate(cards):
        x0 = 110 + idx * 334
        draw.rounded_rectangle([x0, 424, x0 + 310, 524], radius=14, fill="#F9FAFB", outline="#E5E7EB", width=2)
        draw.text((x0 + 22, 444), lbl, fill="#6B7280", font=f_stat_lbl)
        draw.text((x0 + 22, 474), val, fill=col, font=f_stat_val)

    img.save(BASE_DIR / "og-image.png", "PNG", optimize=True)


def generate_headers() -> None:
    content = """/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin

/data/states.json
  Cache-Control: public, max-age=3600
"""
    write_text("_headers", content)


def render_head(
    title: str,
    description: str,
    canonical_path: str,
    schema_json: str = "",
    noindex: bool = False,
) -> str:
    canonical_url = f"{SITE_URL}{canonical_path}"
    robots_tag = '<meta name="robots" content="noindex, follow">' if noindex else '<meta name="robots" content="index, follow">'
    schema_block = f'\n  <script type="application/ld+json">\n{schema_json}\n  </script>' if schema_json else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
  {robots_tag}
  <link rel="canonical" href="{canonical_url}">
  <link rel="icon" type="image/svg+xml" href="/favicon.svg">
  <meta name="theme-color" content="#F38020">
  <meta name="application-name" content="{SITE_NAME}">
  <meta property="og:site_name" content="{SITE_NAME}">
  <meta property="og:type" content="website">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:image" content="{SITE_URL}/og-image.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{html.escape(title)}">
  <meta name="twitter:description" content="{html.escape(description)}">
  <meta name="twitter:image" content="{SITE_URL}/og-image.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="preconnect" href="https://cdnjs.cloudflare.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Outfit:wght@600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" crossorigin="anonymous" referrerpolicy="no-referrer">
  <link rel="stylesheet" href="/style.css">
  <script src="/script.js" defer></script>{schema_block}
</head>"""


def render_header(is_tool_page: bool = True) -> str:
    cta_href = "#auditor-form" if is_tool_page else "/#auditor-form"
    faq_href = "#faq" if is_tool_page else "/#faq"
    states_href = "/#all-states"

    return f"""<header class="site-header">
  <div class="container header-inner">
    <a href="/" class="brand-logo" aria-label="CarQuoteCheck Home">
      <i class="fa-solid fa-shield-halved" aria-hidden="true"></i>
      <span>CarQuote<span class="brand-accent">Check</span></span>
    </a>

    <nav class="desktop-nav" aria-label="Primary Navigation">
      <a href="{states_href}">All 50 States</a>
      <button type="button" class="nav-link-btn js-open-compare">
        <span>Saved Quotes</span>
        <span class="saved-badge js-saved-count">0</span>
      </button>
      <a href="{faq_href}">FAQ</a>
      <a href="/about/">About</a>
    </nav>

    <a href="{cta_href}" class="header-cta">
      <i class="fa-solid fa-magnifying-glass-dollar" aria-hidden="true"></i>
      <span>Audit Quote</span>
    </a>

    <button type="button" id="mobile-menu-btn" class="mobile-menu-btn" aria-label="Toggle navigation menu" aria-expanded="false" aria-controls="mobile-drawer">
      <i class="fa-solid fa-bars" aria-hidden="true"></i>
    </button>
  </div>

  <div id="mobile-drawer" class="mobile-drawer" aria-label="Mobile Navigation">
    <div class="mobile-drawer-links">
      <a href="{states_href}"><span>All 50 States</span><i class="fa-solid fa-chevron-right" aria-hidden="true"></i></a>
      <button type="button" class="mobile-nav-btn js-open-compare">
        <span>Saved Quotes</span>
        <span class="saved-badge js-saved-count">0</span>
      </button>
      <a href="{faq_href}"><span>FAQ</span><i class="fa-solid fa-chevron-right" aria-hidden="true"></i></a>
      <a href="/about/"><span>About</span><i class="fa-solid fa-chevron-right" aria-hidden="true"></i></a>
      <a href="{cta_href}" class="mobile-drawer-cta">
        <i class="fa-solid fa-magnifying-glass-dollar" aria-hidden="true"></i>
        <span>Audit Quote</span>
      </a>
    </div>
  </div>
</header>"""


def render_state_search_bar(placeholder: str = "Search any US state or DC (e.g., Florida, CA, Texas)...") -> str:
    return f"""<div class="state-search-wrap">
  <div class="state-search-input-box">
    <i class="fa-solid fa-magnifying-glass" aria-hidden="true"></i>
    <input type="search" class="state-search-input js-state-search-input" placeholder="{html.escape(placeholder)}" aria-label="Search US states and Washington DC doc fee calculators" autocomplete="off">
  </div>
  <div class="state-search-dropdown" role="listbox" aria-label="Matching states"></div>
</div>"""


def render_calculator_and_results(show_quick_states: bool = True) -> str:
    quick_states_html = ""
    if show_quick_states:
        quick_states_html = """<div class="quick-chips-row" aria-label="Popular states">
      <span class="quick-chips-label">Popular:</span>
      <button type="button" class="chip-btn js-quick-state" data-state="CA">CA ($85 Cap)</button>
      <button type="button" class="chip-btn js-quick-state" data-state="FL">FL (Uncapped)</button>
      <button type="button" class="chip-btn js-quick-state" data-state="TX">TX ($225)</button>
      <button type="button" class="chip-btn js-quick-state" data-state="NY">NY ($175 Cap)</button>
      <button type="button" class="chip-btn js-quick-state" data-state="VA">VA (Uncapped)</button>
      <button type="button" class="chip-btn js-quick-state" data-state="GA">GA (7% TAVT)</button>
    </div>"""

    return f"""<section class="tool-section" aria-label="Car Quote OTD Auditor">
  <div class="container">
    <div class="calc-container">
      <form id="auditor-form" class="card" novalidate>
        <div class="calc-header">
          <h2 class="calc-title"><i class="fa-solid fa-file-invoice-dollar" aria-hidden="true"></i> Enter Dealer Quote Details</h2>
          <div class="calc-actions-top">
            <button type="button" id="btn-sample-quote" class="btn-ghost btn-ghost-accent">
              <i class="fa-solid fa-bolt" aria-hidden="true"></i> Try Sample Quote
            </button>
            <button type="button" id="btn-reset-quote" class="btn-ghost">
              <i class="fa-solid fa-rotate-left" aria-hidden="true"></i> Reset
            </button>
          </div>
        </div>

        {quick_states_html}

        <div id="state-alert-banner" class="state-alert-banner" role="region" aria-label="State rule summary"></div>

        <div class="form-grid">
          <div class="form-group full-width">
            <label for="state-select" class="form-label">
              <span>Purchase / Registration State</span>
              <span class="form-hint">50 States + DC</span>
            </label>
            <select id="state-select" class="form-control" required>
              <option value="">Loading US jurisdictions...</option>
            </select>
          </div>

          <div class="form-group">
            <label for="vehicle-price" class="form-label">
              <span>Vehicle Selling Price</span>
              <span class="form-hint">Required</span>
            </label>
            <div class="input-wrap">
              <span class="input-prefix">$</span>
              <input type="number" id="vehicle-price" class="form-control has-prefix" min="0" step="1" placeholder="32000" required>
            </div>
          </div>

          <div class="form-group">
            <label for="trade-in" class="form-label">
              <span>Trade-In Value</span>
              <span class="form-hint">Optional</span>
            </label>
            <div class="input-wrap">
              <span class="input-prefix">$</span>
              <input type="number" id="trade-in" class="form-control has-prefix" min="0" step="1" placeholder="0">
            </div>
          </div>

          <div class="form-group">
            <label for="doc-fee" class="form-label">
              <span>Dealer Doc / Admin Fee</span>
              <span class="form-hint">Auto-filled avg</span>
            </label>
            <div class="input-wrap">
              <span class="input-prefix">$</span>
              <input type="number" id="doc-fee" class="form-control has-prefix" min="0" step="1" placeholder="499">
            </div>
          </div>

          <div class="form-group">
            <label for="tax-rate" class="form-label">
              <span>Combined Sales Tax Rate</span>
              <span class="form-hint">Editable %</span>
            </label>
            <div class="input-wrap">
              <input type="number" id="tax-rate" class="form-control has-suffix" min="0" max="20" step="0.01" placeholder="7.00">
              <span class="input-suffix">%</span>
            </div>
          </div>

          <div class="form-group full-width">
            <label for="title-reg-fee" class="form-label">
              <span>Gov Title, License &amp; Registration Fee</span>
              <span class="form-hint">Exempt from sales tax</span>
            </label>
            <div class="input-wrap">
              <span class="input-prefix">$</span>
              <input type="number" id="title-reg-fee" class="form-control has-prefix" min="0" step="1" placeholder="250">
            </div>
          </div>
        </div>

        <div class="addons-box">
          <div class="addons-header">
            <h3><i class="fa-solid fa-tags" aria-hidden="true"></i> Dealer Add-Ons &amp; Extra Fees</h3>
            <button type="button" id="btn-add-addon" class="btn-ghost">
              <i class="fa-solid fa-plus" aria-hidden="true"></i> Add Fee / Add-on
            </button>
          </div>
          <div class="quick-chips-row" aria-label="Common dealer junk fees">
            <span class="quick-chips-label">Quick add:</span>
            <button type="button" class="chip-btn js-quick-addon" data-addon="VIN Etching" data-amount="399">+ VIN Etching</button>
            <button type="button" class="chip-btn js-quick-addon" data-addon="Paint Protection" data-amount="895">+ Paint Protection</button>
            <button type="button" class="chip-btn js-quick-addon" data-addon="Nitrogen Tires" data-amount="199">+ Nitrogen Tires</button>
            <button type="button" class="chip-btn js-quick-addon" data-addon="Dealer Prep" data-amount="695">+ Dealer Prep</button>
            <button type="button" class="chip-btn js-quick-addon" data-addon="Market Adjustment" data-amount="2500">+ Market Adjustment</button>
            <button type="button" class="chip-btn js-quick-addon" data-addon="LoJack" data-amount="995">+ LoJack</button>
          </div>
          <div id="addons-list" class="addons-list"></div>
        </div>

        <div class="finance-toggle-box">
          <label class="switch-label" for="finance-toggle">
            <span class="switch-label-text">
              <i class="fa-solid fa-calculator" aria-hidden="true"></i>
              <span>Financing this car? Reveal the Hidden Loan Trap</span>
            </span>
            <input type="checkbox" id="finance-toggle" class="toggle-checkbox">
          </label>
          <div id="finance-fields" class="finance-fields">
            <div class="form-group">
              <label for="down-payment" class="form-label"><span>Down Payment</span></label>
              <div class="input-wrap">
                <span class="input-prefix">$</span>
                <input type="number" id="down-payment" class="form-control has-prefix" min="0" step="100" value="0">
              </div>
            </div>
            <div class="form-group">
              <label for="loan-apr" class="form-label"><span>APR (%)</span></label>
              <div class="input-wrap">
                <input type="number" id="loan-apr" class="form-control has-suffix" min="0" max="35" step="0.1" value="6.5">
                <span class="input-suffix">%</span>
              </div>
            </div>
            <div class="form-group">
              <label for="loan-term" class="form-label"><span>Term (Months)</span></label>
              <input type="number" id="loan-term" class="form-control" min="12" max="96" step="12" value="60">
            </div>
          </div>
        </div>

        <div id="form-error" class="form-error" role="alert"></div>

        <button type="submit" class="btn-primary-cta">
          <i class="fa-solid fa-magnifying-glass-dollar" aria-hidden="true"></i>
          <span>Audit My Quote</span>
        </button>
      </form>

      <!-- Button-Triggered Results Dashboard -->
      <section id="audit-results" class="card results-section" aria-live="polite" aria-label="Quote Audit Results">
        <div class="results-top-grid">
          <div class="metric-box">
            <div class="metric-label">Deal Fairness Score</div>
            <div id="res-score-val" class="metric-value">-- / 100</div>
            <div class="score-bar-track"><div id="res-score-bar" class="score-bar-fill" style="width:0%"></div></div>
            <div id="res-score-verdict" class="metric-sub">--</div>
          </div>
          <div class="metric-box">
            <div class="metric-label">Quoted OTD Price</div>
            <div id="res-quoted-otd" class="metric-value">$0</div>
            <div id="res-quoted-sub" class="metric-sub">--</div>
          </div>
          <div class="metric-box">
            <div class="metric-label">Fair Target OTD</div>
            <div id="res-fair-otd" class="metric-value" style="color:var(--safe);">$0</div>
            <div id="res-fair-sub" class="metric-sub">--</div>
          </div>
        </div>

        <div id="res-savings-banner" class="savings-banner"></div>

        <h3 class="breakdown-heading"><i class="fa-solid fa-list-check" aria-hidden="true"></i> Traffic-Light Line-by-Line Audit</h3>
        <div class="table-scroll">
          <table class="audit-table">
            <thead>
              <tr>
                <th>Line Item &amp; Audit Note</th>
                <th>Status</th>
                <th class="col-right">Amount</th>
              </tr>
            </thead>
            <tbody id="res-breakdown-body"></tbody>
          </table>
        </div>

        <div id="res-loan-trap" class="loan-trap-box">
          <h3 class="breakdown-heading" style="margin-bottom:6px;color:#B45309;"><i class="fa-solid fa-percent" aria-hidden="true"></i> Hidden Loan Trap Impact</h3>
          <p style="margin:0;font-size:0.88rem;color:var(--text-secondary);">Rolling junk fees and excess doc fees into your auto loan forces you to pay compound interest on dealership markups.</p>
          <div class="loan-trap-grid">
            <div class="loan-stat">
              <div class="loan-stat-label">Quoted Monthly</div>
              <div id="loan-quoted-mo" class="loan-stat-val">$0.00/mo</div>
            </div>
            <div class="loan-stat">
              <div class="loan-stat-label">Fair Target Monthly</div>
              <div id="loan-fair-mo" class="loan-stat-val" style="color:var(--safe);">$0.00/mo</div>
            </div>
            <div class="loan-stat">
              <div class="loan-stat-label">Extra Interest on Junk</div>
              <div id="loan-extra-int" class="loan-stat-val" style="color:var(--danger);">$0</div>
            </div>
            <div class="loan-stat">
              <div class="loan-stat-label">Total Financed Waste</div>
              <div id="loan-total-trap" class="loan-stat-val" style="color:var(--danger);">$0</div>
            </div>
          </div>
        </div>

        <div class="action-bar">
          <button type="button" id="btn-save-quote" class="btn-action btn-action-dark">
            <i class="fa-solid fa-scale-balanced" aria-hidden="true"></i> Save &amp; Compare Quote
          </button>
          <button type="button" id="btn-download-png" class="btn-action">
            <i class="fa-solid fa-image" aria-hidden="true"></i> Download Audit Card PNG
          </button>
          <button type="button" id="btn-share-link" class="btn-action">
            <i class="fa-solid fa-link" aria-hidden="true"></i> Copy Shareable Link
          </button>
          <button type="button" id="btn-print-sheet" class="btn-action">
            <i class="fa-solid fa-print" aria-hidden="true"></i> Print 1-Page Sheet
          </button>
        </div>

        <div class="email-panel">
          <div class="email-panel-header">
            <h3 class="breakdown-heading" style="margin:0;"><i class="fa-solid fa-envelope-open-text" aria-hidden="true"></i> 1-Click Counter-Offer Email</h3>
            <div class="tone-tabs" role="tablist" aria-label="Counter-offer email tone">
              <button type="button" class="tone-tab js-tone-tab is-active" data-tone="polite">Polite</button>
              <button type="button" class="tone-tab js-tone-tab" data-tone="firm">Firm</button>
              <button type="button" class="tone-tab js-tone-tab" data-tone="walkaway">Walk-Away</button>
            </div>
          </div>
          <textarea id="counter-email-text" class="email-textarea" readonly aria-label="Generated counter-offer email text"></textarea>
          <div style="margin-top:10px;display:flex;justify-content:flex-end;">
            <button type="button" id="btn-copy-email" class="btn-action">
              <i class="fa-regular fa-copy" aria-hidden="true"></i> Copy Counter-Offer Email
            </button>
          </div>
        </div>

        <!-- Non-Intrusive Affiliate / Partner Next Step Card (Replace # URLs with affiliate links) -->
        <div class="partner-card">
          <div class="partner-card-header">
            <h3 class="breakdown-heading" style="margin:0;"><i class="fa-solid fa-piggy-bank" aria-hidden="true"></i> Next Step: Save on Auto Insurance &amp; Auto Loans</h3>
            <span class="badge badge-neutral">Partner Offers</span>
          </div>
          <div class="partner-grid">
            <div class="partner-item">
              <div>
                <h4>Compare Pre-Approved Auto Loan Rates</h4>
                <p>Walk into the F&amp;I office with a credit union or online pre-approval so the dealer cannot mark up your APR.</p>
              </div>
              <!-- AFFILIATE_LINK_AUTO_LOAN: Replace # below with your partner URL -->
              <a href="#" class="partner-cta" rel="sponsored nofollow">Check Today's Auto Loan Rates <i class="fa-solid fa-arrow-right" aria-hidden="true"></i></a>
            </div>
            <div class="partner-item">
              <div>
                <h4>Compare Full-Coverage Auto Insurance</h4>
                <p>Quote multiple carriers before signing so you know your true monthly ownership cost and avoid dealer GAP markups.</p>
              </div>
              <!-- AFFILIATE_LINK_AUTO_INSURANCE: Replace # below with your partner URL -->
              <a href="#" class="partner-cta" rel="sponsored nofollow">Compare Auto Insurance Quotes <i class="fa-solid fa-arrow-right" aria-hidden="true"></i></a>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</section>"""


def render_how_it_works() -> str:
    return """<section class="content-section" aria-label="How CarQuoteCheck works">
  <div class="container">
    <div class="section-header">
      <h2>How CarQuoteCheck Protects Your Wallet</h2>
      <p>Three steps to turn a confusing dealership worksheet into a clear Out-the-Door counter-offer.</p>
    </div>
    <div class="steps-grid">
      <div class="step-card">
        <div class="step-icon"><i class="fa-solid fa-map-location-dot" aria-hidden="true"></i></div>
        <h3>1. Apply Exact State Rules</h3>
        <p>Select any of the 50 US states or DC to load statutory doc fee caps, doc fee taxability, and trade-in tax credit rules instantly.</p>
      </div>
      <div class="step-card">
        <div class="step-icon"><i class="fa-solid fa-radar" aria-hidden="true"></i></div>
        <h3>2. Flag 55+ Dealer Junk Fees</h3>
        <p>Enter add-ons like VIN etching, paint protection, or market adjustments to see which fees are mandatory government costs and which are pure markup.</p>
      </div>
      <div class="step-card">
        <div class="step-icon"><i class="fa-solid fa-paper-plane" aria-hidden="true"></i></div>
        <h3>3. Send a Clean Counter-Offer</h3>
        <p>Copy a tailored Polite, Firm, or Walk-Away email with your Fair Target OTD, or save up to 4 dealer quotes side by side.</p>
      </div>
    </div>
  </div>
</section>"""


def render_checklist() -> str:
    items = [
        ("Demand an Itemized Out-the-Door (OTD) Buyer's Order", "Never negotiate by monthly payment alone; require every fee and tax line in writing."),
        ("Compare Add-Ons Against the Factory Window Sticker", "Verify floor mats, tint, or destination charges are not being billed twice by the dealer."),
        ("Verify the State Statutory Doc Fee Cap", "If your state caps documentation fees, dealers cannot legally exceed that amount."),
        ("Bring a Pre-Approved Auto Loan Rate", "A credit union or bank pre-approval stops F&I managers from inflating your interest rate."),
        ("Decline Optional F&I Products Until You Research", "Extended warranties, GAP, and tire plans are never legally required for loan approval."),
    ]
    rows = "\n".join(
        f"""      <label class="checklist-item">
        <input type="checkbox">
        <div><strong>{html.escape(t)}</strong><span>{html.escape(d)}</span></div>
      </label>"""
        for t, d in items
    )
    return f"""<section class="content-section" aria-label="Showroom Red-Flag Checklist">
  <div class="container">
    <div class="checklist-card">
      <h2 style="margin:0 0 6px;font-size:1.35rem;"><i class="fa-solid fa-clipboard-check" style="color:var(--brand);margin-right:8px;" aria-hidden="true"></i>5-Point Showroom Red-Flag Checklist</h2>
      <p style="margin:0;color:var(--text-secondary);font-size:0.92rem;">Check off each step before signing your final retail installment contract.</p>
      <div class="checklist-items">
{rows}
      </div>
    </div>
  </div>
</section>"""


def render_faq_section(faqs: list) -> str:
    items_html = []
    for idx, (q, a) in enumerate(faqs):
        open_cls = " is-open" if idx == 0 else ""
        expanded = "true" if idx == 0 else "false"
        items_html.append(f"""      <div class="faq-item{open_cls}">
        <button type="button" class="faq-trigger" aria-expanded="{expanded}">
          <span>{html.escape(q)}</span>
          <i class="fa-solid fa-chevron-down" aria-hidden="true"></i>
        </button>
        <div class="faq-panel">{html.escape(a)}</div>
      </div>""")
    return f"""<section id="faq" class="content-section" aria-label="Frequently Asked Questions">
  <div class="container">
    <div class="section-header">
      <h2>Frequently Asked Questions</h2>
      <p>Clear, plain-English answers on car dealership doc fees, sales tax, and OTD pricing.</p>
    </div>
    <div class="faq-list">
{"".join(items_html)}
    </div>
  </div>
</section>"""


def render_footer_and_modal() -> str:
    return """<footer class="site-footer">
  <div class="container">
    <div class="footer-inner">
      <a href="/" class="brand-logo" aria-label="CarQuoteCheck Home">
        <i class="fa-solid fa-shield-halved" aria-hidden="true"></i>
        <span>CarQuote<span class="brand-accent">Check</span></span>
      </a>
      <nav class="footer-links" aria-label="Footer Navigation">
        <a href="/about/">About &amp; Methodology</a>
        <a href="/privacy-policy/">Privacy Policy</a>
        <a href="/terms-of-service/">Terms of Service</a>
        <a href="/contact/">Contact</a>
      </nav>
      <div class="footer-note">
        <span>100% client-side browser tool. No quotes are uploaded to any server.</span>
        <span>Informational &amp; educational use only — not legal, tax, or financial advice.</span>
      </div>
    </div>
  </div>
</footer>

<!-- Multi-Dealer Quote Comparator Modal -->
<div id="compare-modal" class="modal-backdrop" role="dialog" aria-modal="true" aria-hidden="true" aria-labelledby="compare-modal-title">
  <div class="modal-dialog">
    <div class="modal-header">
      <h2 id="compare-modal-title"><i class="fa-solid fa-scale-balanced" style="color:var(--brand);margin-right:8px;" aria-hidden="true"></i>Saved Dealer Quotes Comparator</h2>
      <button type="button" class="modal-close" aria-label="Close comparator modal">
        <i class="fa-solid fa-xmark" aria-hidden="true"></i>
      </button>
    </div>
    <div id="compare-modal-body"></div>
  </div>
</div>
</body>
</html>"""


def build_schema_graph(
    canonical_path: str,
    app_name: str,
    app_desc: str,
    faqs: list,
    breadcrumb_state_name: str = "",
) -> str:
    url = f"{SITE_URL}{canonical_path}"
    graph = [
        {
            "@type": "WebSite",
            "@id": f"{SITE_URL}/#website",
            "url": f"{SITE_URL}/",
            "name": SITE_NAME,
            "description": "Free 50-state US car dealership Out-the-Door (OTD) price and dealer junk-fee auditor.",
        },
        {
            "@type": "WebApplication",
            "@id": f"{url}#webapp",
            "name": app_name,
            "url": url,
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "Any",
            "description": app_desc,
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
            },
        },
    ]

    if breadcrumb_state_name:
        graph.append({
            "@type": "BreadcrumbList",
            "@id": f"{url}#breadcrumb",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": f"{SITE_URL}/",
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": f"{breadcrumb_state_name} Doc Fee Calculator",
                    "item": url,
                },
            ],
        })

    if faqs:
        graph.append({
            "@type": "FAQPage",
            "@id": f"{url}#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": a,
                    },
                }
                for q, a in faqs
            ],
        })

    return json.dumps({"@context": "https://schema.org", "@graph": graph}, indent=2)


def generate_homepage(states: list) -> None:
    title = "Car OTD Price & Dealer Junk Fee Auditor | CarQuoteCheck"
    desc = "Audit any US car dealership quote in seconds. Check 50-state + DC doc fee caps, verify sales tax and trade-in credits, flag 55+ junk fees, and generate counter-offer emails."

    faqs = [
        (
            "What is an Out-the-Door (OTD) car price?",
            "An Out-the-Door (OTD) price is the complete, final total you pay to drive a vehicle off the dealership lot. It includes the vehicle selling price, dealer documentation fee, any add-ons, state and local sales tax, and official DMV title and registration fees.",
        ),
        (
            "Are car dealer documentation fees legally capped in every state?",
            "No. Roughly one-third of US states enforce a statutory cap on dealer doc fees, ranging from $85 in California to $800 in Maryland. Uncapped states like Florida, Virginia, and Georgia allow dealers to set their own doc fees, often $799 to $1,199.",
        ),
        (
            "Which car dealership fees are mandatory vs. negotiable junk fees?",
            "Only state/local sales tax and official DMV title, license, and registration fees are mandatory by law. Dealer add-ons like VIN etching, nitrogen tires, paint protection, dealer prep, and market adjustments are optional profit markups you can decline or negotiate.",
        ),
        (
            "Does a trade-in reduce my car sales tax?",
            "In most US states, your trade-in value is deducted from the vehicle selling price before sales tax is calculated. However, states including California, Virginia, Maryland, Hawaii, and Washington, DC do not offer a trade-in sales tax credit.",
        ),
        (
            "Is my car quote data uploaded or shared with dealerships?",
            "Never. CarQuoteCheck runs 100% inside your web browser using local JavaScript. Your numbers are never sent to a server, sold as dealer leads, or stored online. Saved quotes live only in your device's localStorage.",
        ),
    ]

    schema_json = build_schema_graph("/", title, desc, faqs)

    table_rows = []
    for s in states:
        cap_cell = fmt_cap_badge(s)
        trade_cell = '<span class="badge badge-safe">Yes</span>' if s["trade_in_tax_credit"] else '<span class="badge badge-danger">No</span>'
        tax_doc_cell = "Yes" if s["doc_fee_taxable"] else "No"
        table_rows.append(
            f"""            <tr>
              <td><a href="/{s["slug"]}/"><strong>{html.escape(s["name"])}</strong> ({s["code"]})</a></td>
              <td>{cap_cell}</td>
              <td class="tabular-nums">${s["avg_doc_fee"]}</td>
              <td class="tabular-nums">{s["avg_combined_tax_pct"]:.2f}%</td>
              <td>{tax_doc_cell}</td>
              <td>{trade_cell}</td>
              <td><a href="/{s["slug"]}/">Audit {s["code"]} <i class="fa-solid fa-arrow-right" aria-hidden="true"></i></a></td>
            </tr>"""
        )

    directory_html = f"""<section id="all-states" class="content-section" aria-label="50-State and DC Car Dealer Doc Fee Directory">
  <div class="container">
    <div class="section-header">
      <h2>All 50 States + DC Car Dealer Doc Fee Caps &amp; Tax Rules</h2>
      <p>Compare statutory documentation fee limits, average combined vehicle tax rates, and trade-in tax credits nationwide.</p>
    </div>
    <div class="directory-controls">
      <input type="search" id="directory-filter" class="directory-filter-input" placeholder="Filter table by state name or code..." aria-label="Filter 50-state table">
      <span class="badge badge-neutral">51 US Jurisdictions Indexed</span>
    </div>
    <div class="table-scroll">
      <table class="directory-table">
        <thead>
          <tr>
            <th>State / Jurisdiction</th>
            <th>Doc Fee Cap</th>
            <th>Avg Doc Fee</th>
            <th>Avg Tax Rate</th>
            <th>Doc Fee Taxed</th>
            <th>Trade-In Credit</th>
            <th>Calculator</th>
          </tr>
        </thead>
        <tbody id="directory-table-body">
{"".join(table_rows)}
        </tbody>
      </table>
    </div>
  </div>
</section>"""

    page = (
        render_head(title, desc, "/", schema_json)
        + '\n<body data-default-state="">\n'
        + render_header(is_tool_page=True)
        + """<main>
  <section class="hero">
    <div class="container">
      <div class="trust-pill"><i class="fa-solid fa-lock" aria-hidden="true"></i> 100% Free &bull; No Login &bull; Private Browser Tool</div>
      <h1>Spot Car Dealer Junk Fees Before You Sign</h1>
      <p class="hero-sub">Verify Out-the-Door pricing, statutory doc fee caps, and sales tax across all 50 US states and Washington, DC.</p>
      """
        + render_state_search_bar()
        + """
    </div>
  </section>
"""
        + render_calculator_and_results(show_quick_states=True)
        + render_how_it_works()
        + directory_html
        + render_checklist()
        + render_faq_section(faqs)
        + "</main>\n"
        + render_footer_and_modal()
    )
    write_text("index.html", page)


def generate_state_pages(states: list) -> None:
    states_map = {s["code"]: s for s in states}

    for st in states:
        code = st["code"]
        name = st["name"]
        slug = st["slug"]
        canonical_path = f"/{slug}/"

        title = f"{name} Car Dealer Doc Fee & OTD Price Calculator | CarQuoteCheck"
        cap_phrase = f"${st['doc_fee_cap']} legal doc fee cap" if st["doc_fee_cap"] is not None else f"uncapped doc fees (avg ${st['avg_doc_fee']})"
        desc = (
            f"Audit any {name} car dealership Out-the-Door (OTD) quote. Check {name}'s {cap_phrase}, "
            f"{st['avg_combined_tax_pct']:.2f}% avg vehicle tax rate, trade-in credit rules, and flag hidden dealer junk fees."
        )

        if st["doc_fee_cap"] is not None:
            q1_ans = f"Yes. {name} enforces a statutory cap of ${st['doc_fee_cap']} on car dealer documentation fees. If a {name} dealership charges more than ${st['doc_fee_cap']} for doc or admin processing, you should challenge the overcharge immediately."
        else:
            q1_ans = f"No. {name} does not set a statutory cap on dealer documentation fees. Dealerships in {name} typically charge around ${st['avg_doc_fee']}, so buyers should negotiate the vehicle selling price down to offset high doc fees."

        q2_ans = (
            f"Yes, dealer documentation fees in {name} are subject to motor vehicle sales or excise tax. Including the doc fee in your taxable base increases your final Out-the-Door cost."
            if st["doc_fee_taxable"]
            else f"No, dealer documentation fees in {name} are generally excluded from the vehicle sales tax calculation, though you should still verify the itemized buyer's order."
        )

        q3_ans = (
            f"Yes. {name} offers a trade-in sales tax credit, meaning your trade-in allowance is deducted from the vehicle selling price before calculating the {st['avg_combined_tax_pct']:.2f}% average combined tax."
            if st["trade_in_tax_credit"]
            else f"No. {name} does not provide a trade-in sales tax credit, so vehicle tax is calculated on the full selling price even when you trade in your current car."
        )

        q4_ans = f"Average combined vehicle tax in {name} is roughly {st['avg_combined_tax_pct']:.2f}% (state base {st['state_sales_tax_pct']:.2f}%), plus about ${st['avg_title_reg_fee']} for official title and registration. Local rates vary by county, such as {st['major_counties_example']}."

        faqs = [
            (f"Is there a legal cap on car dealer doc fees in {name}?", q1_ans),
            (f"Are dealer doc fees taxable in {name}?", q2_ans),
            (f"Does {name} offer a trade-in sales tax credit on cars?", q3_ans),
            (f"How much are car sales tax and DMV fees in {name}?", q4_ans),
        ]

        schema_json = build_schema_graph(canonical_path, title, desc, faqs, breadcrumb_state_name=name)

        cap_stat = f"${st['doc_fee_cap']} Statutory Cap" if st["doc_fee_cap"] is not None else f"No Legal Cap (Avg ${st['avg_doc_fee']})"
        trade_stat = "Yes — reduces taxable amount" if st["trade_in_tax_credit"] else "No — tax applies to full selling price"
        doc_tax_stat = "Yes — taxed with vehicle" if st["doc_fee_taxable"] else "No — excluded from sales tax"

        state_guide_html = f"""<section class="content-section" aria-label="{html.escape(name)} Car Buying Tax and Doc Fee Guide">
  <div class="container">
    <div class="section-header">
      <h2>{html.escape(name)} Car Dealership Fee &amp; Tax Rules</h2>
      <p>Key statutory benchmarks and local county examples to verify on your {html.escape(name)} buyer's order.</p>
    </div>
    <div class="state-guide-grid">
      <div class="info-card">
        <h3><i class="fa-solid fa-gavel" aria-hidden="true"></i> {html.escape(name)} Fee &amp; Tax Summary</h3>
        <ul class="info-list">
          <li><strong>Dealer Doc Fee Rule:</strong> {html.escape(cap_stat)}</li>
          <li><strong>Doc Fee Taxability:</strong> {html.escape(doc_tax_stat)}</li>
          <li><strong>State / Avg Combined Tax:</strong> {st["state_sales_tax_pct"]:.2f}% base / ~{st["avg_combined_tax_pct"]:.2f}% combined</li>
          <li><strong>Trade-In Tax Credit:</strong> {html.escape(trade_stat)}</li>
          <li><strong>Est. DMV Title &amp; Reg:</strong> ~${st["avg_title_reg_fee"]} (varies by weight/value)</li>
        </ul>
      </div>
      <div class="info-card">
        <h3><i class="fa-solid fa-location-dot" aria-hidden="true"></i> Local County Examples &amp; Alert</h3>
        <p style="margin:0 0 12px;color:var(--text-secondary);font-size:0.94rem;"><strong>Major Counties:</strong> {html.escape(st["major_counties_example"])}</p>
        <p style="margin:0;color:var(--text-secondary);font-size:0.94rem;"><strong>Buyer Watchout:</strong> {html.escape(st["special_alert"])}</p>
      </div>
    </div>
  </div>
</section>"""

        nearby_cards = []
        for nb_code in st["nearby_states"]:
            nb = states_map[nb_code]
            nearby_cards.append(
                f"""      <a class="nearby-card" href="/{nb["slug"]}/">
        <div class="nearby-card-top">
          <span>{html.escape(nb["name"])} ({nb["code"]})</span>
          <i class="fa-solid fa-arrow-right" style="color:var(--brand);" aria-hidden="true"></i>
        </div>
        <div>{fmt_cap_badge(nb)}</div>
        <div class="nearby-card-meta">Avg Tax: {nb["avg_combined_tax_pct"]:.2f}% &bull; Trade Credit: {"Yes" if nb["trade_in_tax_credit"] else "No"}</div>
      </a>"""
            )

        nearby_html = f"""<section class="content-section" aria-label="Compare Nearby States">
  <div class="container">
    <div class="section-header">
      <h2>Compare Nearby States to {html.escape(name)}</h2>
      <p>Buying across state lines? Compare documentation fee caps and tax rules in neighboring jurisdictions.</p>
    </div>
    <div class="nearby-grid">
{"".join(nearby_cards)}
    </div>
  </div>
</section>"""

        page = (
            render_head(title, desc, canonical_path, schema_json)
            + f'\n<body data-default-state="{code}">\n'
            + render_header(is_tool_page=True)
            + f"""<main>
  <section class="hero">
    <div class="container">
      <nav class="breadcrumbs" aria-label="Breadcrumb">
        <a href="/">Home</a>
        <span class="sep"><i class="fa-solid fa-chevron-right" aria-hidden="true"></i></span>
        <span aria-current="page">{html.escape(name)} Doc Fee Calculator</span>
      </nav>
      <div><span class="trust-pill"><i class="fa-solid fa-lock" aria-hidden="true"></i> 100% Free &bull; No Login &bull; Private Browser Tool</span></div>
      <h1>{html.escape(name)} Car Dealer Doc Fee &amp; OTD Auditor</h1>
      <p class="hero-sub">Check {html.escape(name)}'s {html.escape(cap_phrase)}, estimate local vehicle taxes, and strip dealer junk fees before you sign.</p>
      """
            + render_state_search_bar(f"Switch state (currently {name})...")
            + """
    </div>
  </section>
"""
            + render_calculator_and_results(show_quick_states=False)
            + state_guide_html
            + nearby_html
            + render_checklist()
            + render_faq_section(faqs)
            + "</main>\n"
            + render_footer_and_modal()
        )
        write_text(f"{slug}/index.html", page)


def generate_legal_and_trust_pages() -> None:
    # 1. Privacy Policy
    priv_title = "Privacy Policy | CarQuoteCheck"
    priv_desc = "CarQuoteCheck runs 100% client-side in your browser with zero server uploads. Learn how we protect your privacy."
    priv_body = """<section class="hero"><div class="container">
      <div class="trust-pill"><i class="fa-solid fa-shield-halved" aria-hidden="true"></i> Zero Server Uploads</div>
      <h1>Privacy Policy</h1>
      <p class="hero-sub">Your car quote numbers stay strictly inside your web browser.</p>
    </div></section>
    <div class="container"><article class="prose-card">
      <h2>100% Client-Side Processing</h2>
      <p>CarQuoteCheck is a static, client-side web application. Every vehicle price, trade-in allowance, documentation fee, add-on, and financing input you enter is processed exclusively in your browser's local memory using JavaScript. We do not have a backend database and never transmit your quote inputs to our servers or to any car dealership.</p>
      <h2>Local Storage Only</h2>
      <p>When you click <strong>Save &amp; Compare Quote</strong>, your saved quotes are stored locally on your own device using your browser's <code>localStorage</code> API. You can delete individual quotes inside the Saved Quotes modal or clear your browser site data at any time.</p>
      <h2>Shareable Audit Links</h2>
      <p>If you choose to click <strong>Copy Shareable Link</strong>, your numeric quote values are encoded directly into the URL query string so you can share them with family or online forums. Only share links with people you trust.</p>
      <h2>Third-Party Advertising &amp; Affiliate Links</h2>
      <p>CarQuoteCheck may display non-intrusive partner links (such as auto loan or auto insurance comparisons) or privacy-respecting advertisements to keep this tool free. Clicking an external partner link takes you to a third-party website governed by that partner's privacy policy.</p>
      <h2>Contact</h2>
      <p>Questions about privacy? Reach us anytime via our <a href="/contact/">Contact page</a>.</p>
    </article></div>"""
    write_text(
        "privacy-policy/index.html",
        render_head(priv_title, priv_desc, "/privacy-policy/")
        + '\n<body data-default-state="">\n'
        + render_header(is_tool_page=False)
        + f"<main>{priv_body}</main>\n"
        + render_footer_and_modal(),
    )

    # 2. Terms of Service
    tos_title = "Terms of Service | CarQuoteCheck"
    tos_desc = "Terms of use and informational disclaimer for CarQuoteCheck US car dealership OTD and doc fee calculators."
    tos_body = """<section class="hero"><div class="container">
      <div class="trust-pill"><i class="fa-solid fa-scale-balanced" aria-hidden="true"></i> Informational Use Only</div>
      <h1>Terms of Service</h1>
      <p class="hero-sub">Please review these terms before using CarQuoteCheck calculators and templates.</p>
    </div></section>
    <div class="container"><article class="prose-card">
      <h2>Educational &amp; Informational Disclaimer</h2>
      <p>CarQuoteCheck provides vehicle Out-the-Door (OTD) estimates, statutory doc fee summaries, and negotiation email templates strictly for informational and educational purposes. Nothing on this website constitutes legal, tax, financial, or accounting advice.</p>
      <h2>Accuracy of State Tax Rates &amp; Doc Fee Caps</h2>
      <p>State legislatures, county tax assessors, and state DMV offices periodically update documentation fee caps, trade-in tax credit limits, and local municipal tax rates. While we maintain an externalized dataset covering all 50 US states and Washington, DC, always confirm final tax and DMV figures with your local county tax office or state DMV before signing a binding purchase contract.</p>
      <h2>Limitation of Liability</h2>
      <p>CarQuoteCheck is provided "as is" without warranties of any kind. We are not responsible for dealership pricing decisions, contract disputes, financing terms, or discrepancies between our estimates and a dealer's final buyer's order.</p>
      <h2>Affiliate Disclosure</h2>
      <p>Some outbound links to auto finance or auto insurance partners may earn a referral commission at no additional cost to you. Partner relationships never influence our Deal Fairness Score or junk-fee detection rules.</p>
    </article></div>"""
    write_text(
        "terms-of-service/index.html",
        render_head(tos_title, tos_desc, "/terms-of-service/")
        + '\n<body data-default-state="">\n'
        + render_header(is_tool_page=False)
        + f"<main>{tos_body}</main>\n"
        + render_footer_and_modal(),
    )

    # 3. About & Methodology
    about_title = "About & Methodology | CarQuoteCheck"
    about_desc = "How CarQuoteCheck audits US car dealership OTD quotes, scores junk fees, and verifies 50-state + DC doc fee caps."
    about_body = """<section class="hero"><div class="container">
      <div class="trust-pill"><i class="fa-solid fa-magnifying-glass-chart" aria-hidden="true"></i> Transparent Audit Methodology</div>
      <h1>About CarQuoteCheck</h1>
      <p class="hero-sub">Built to give US car buyers instant, private leverage against hidden dealership fees.</p>
    </div></section>
    <div class="container"><article class="prose-card">
      <h2>Why We Built CarQuoteCheck</h2>
      <p>Car buying in the United States often turns opaque the moment a dealership prints a four-square worksheet. Legitimate government taxes and title fees are routinely mixed with optional, high-margin dealer add-ons like VIN etching, nitrogen tires, paint sealants, and inflated documentation fees. CarQuoteCheck separates mandatory costs from negotiable profit in seconds.</p>
      <h2>Our Audit &amp; Scoring Methodology</h2>
      <ul>
        <li><strong>Statutory Doc Fee Verification:</strong> Every quote is checked against our 51-jurisdiction dataset (all 50 states + Washington, DC). Exceeding a state's legal cap triggers an immediate red flag and reduces the Deal Fairness Score.</li>
        <li><strong>55+ Junk-Fee Keyword Radar:</strong> Custom dealer add-ons are classified into Mandatory Government Fees (Green) or Optional Dealer Markups (Red) with clear explanations so you know what to decline.</li>
        <li><strong>Edge-Case Proof Tax &amp; Loan Math:</strong> Taxable amounts respect state-specific trade-in tax credit rules and doc fee taxability, never produce negative tax, exclude government DMV fees from sales tax, and safely compute 0% APR financing.</li>
      </ul>
      <h2>Data Verification &amp; Community Updates</h2>
      <p>All state tax rates, statutory doc fee caps, and county examples are stored in a transparent JSON dataset reviewed periodically against state DMV and Department of Revenue publications. Spot a newly enacted state doc fee cap change? <a href="/contact/">Report it in one click</a>.</p>
    </article></div>"""
    write_text(
        "about/index.html",
        render_head(about_title, about_desc, "/about/")
        + '\n<body data-default-state="">\n'
        + render_header(is_tool_page=False)
        + f"<main>{about_body}</main>\n"
        + render_footer_and_modal(),
    )

    # 4. Contact (Zero-backend: copyable email, mailto:, 1-click Report Outdated Cap template — NO <form>)
    contact_title = "Contact | CarQuoteCheck"
    contact_desc = "Contact CarQuoteCheck or report an outdated US state car dealer doc fee cap or tax rule in one click."
    report_subject = quote("Outdated State Doc Fee Cap Report — CarQuoteCheck")
    report_body = quote(
        "Hi CarQuoteCheck Team,\n\n"
        "I would like to report an updated state rule:\n"
        "- State: [Enter State]\n"
        "- New Doc Fee Cap / Rule: [Enter Amount or Rule]\n"
        "- Official DMV / Statute Link: [Paste URL]\n\n"
        "Thank you!"
    )
    contact_body = f"""<section class="hero"><div class="container">
      <div class="trust-pill"><i class="fa-solid fa-envelope" aria-hidden="true"></i> Direct Email &bull; No Tracking Forms</div>
      <h1>Contact CarQuoteCheck</h1>
      <p class="hero-sub">Help us keep all 50 states + DC accurate, or reach out with feedback and partnerships.</p>
    </div></section>
    <div class="container"><article class="prose-card">
      <div class="contact-grid">
        <div class="contact-box">
          <div>
            <h2 style="margin-top:0;"><i class="fa-solid fa-paper-plane" style="color:var(--brand);margin-right:8px;" aria-hidden="true"></i>General Inquiries</h2>
            <p>Have a feature idea, bug report, or media question? Email us directly anytime.</p>
            <p style="font-weight:700;color:var(--text-primary);">{CONTACT_EMAIL}</p>
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:8px;">
            <a href="mailto:{CONTACT_EMAIL}" class="btn-action btn-action-dark"><i class="fa-solid fa-envelope" aria-hidden="true"></i> Open Email App</a>
            <button type="button" class="btn-action js-copy-email" data-email="{CONTACT_EMAIL}"><i class="fa-regular fa-copy" aria-hidden="true"></i> Copy Email</button>
          </div>
        </div>
        <div class="contact-box">
          <div>
            <h2 style="margin-top:0;"><i class="fa-solid fa-flag" style="color:var(--brand);margin-right:8px;" aria-hidden="true"></i>Report an Outdated State Cap</h2>
            <p>State legislatures periodically adjust statutory dealer doc fee caps. Send us a quick pre-filled tip with an official source link.</p>
          </div>
          <div>
            <a href="mailto:{CONTACT_EMAIL}?subject={report_subject}&amp;body={report_body}" class="btn-primary-cta" style="margin-top:0;height:46px;font-size:0.95rem;">
              <i class="fa-solid fa-gavel" aria-hidden="true"></i> Report an Outdated State Doc Fee Cap
            </a>
          </div>
        </div>
      </div>
    </article></div>"""
    write_text(
        "contact/index.html",
        render_head(contact_title, contact_desc, "/contact/")
        + '\n<body data-default-state="">\n'
        + render_header(is_tool_page=False)
        + f"<main>{contact_body}</main>\n"
        + render_footer_and_modal(),
    )


def generate_404() -> None:
    title = "Page Not Found | CarQuoteCheck"
    desc = "The page you requested could not be found. Search any US state doc fee calculator or return to CarQuoteCheck."
    body = (
        """<section class="hero" style="padding:64px 0;">
  <div class="container">
    <div class="trust-pill"><i class="fa-solid fa-compass" aria-hidden="true"></i> Error 404</div>
    <h1>We Could Not Find That Page</h1>
    <p class="hero-sub">Search any of the 50 US states or Washington, DC below, or jump straight back to the main OTD Quote Auditor.</p>
    """
        + render_state_search_bar()
        + """
    <div style="margin-top:24px;">
      <a href="/" class="header-cta" style="display:inline-flex;">
        <i class="fa-solid fa-house" aria-hidden="true"></i> Back to CarQuoteCheck Home
      </a>
    </div>
  </div>
</section>"""
    )
    write_text(
        "404.html",
        render_head(title, desc, "/404.html", noindex=True)
        + '\n<body data-default-state="">\n'
        + render_header(is_tool_page=False)
        + f"<main>{body}</main>\n"
        + render_footer_and_modal(),
    )


def generate_crawl_and_ai_files(states: list) -> None:
    robots = f"""User-agent: *
Allow: /

User-agent: Googlebot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: PerplexityBot
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""
    write_text("robots.txt", robots)

    canonical_paths = ["/"] + [f"/{s['slug']}/" for s in states] + [
        "/about/",
        "/privacy-policy/",
        "/terms-of-service/",
        "/contact/",
    ]
    urls_xml = []
    for p in canonical_paths:
        prio = "1.0" if p == "/" else ("0.8" if "-car-dealer-doc-fee-calculator/" in p else "0.5")
        urls_xml.append(
            f"""  <url>
    <loc>{SITE_URL}{p}</loc>
    <changefreq>monthly</changefreq>
    <priority>{prio}</priority>
  </url>"""
        )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls_xml)
        + "\n</urlset>\n"
    )
    write_text("sitemap.xml", sitemap)

    state_lines = []
    for s in states:
        cap = f"${s['doc_fee_cap']} statutory cap" if s["doc_fee_cap"] is not None else f"Uncapped (avg ${s['avg_doc_fee']})"
        credit = "Yes" if s["trade_in_tax_credit"] else "No"
        state_lines.append(
            f"- [{s['name']} ({s['code']}) Doc Fee & OTD Calculator]({SITE_URL}/{s['slug']}/): {cap}, Avg Tax {s['avg_combined_tax_pct']:.2f}%, Trade-In Credit: {credit}"
        )

    llms = f"""# {SITE_NAME}

> Free, 100% client-side US Car Dealership Out-the-Door (OTD) Price & Junk-Fee Auditor covering all 50 US states and Washington, DC.

## Overview
CarQuoteCheck helps US car buyers audit dealership buyer's orders privately in their browser without logins or server uploads. It verifies state statutory documentation fee caps, applies state-specific sales tax and trade-in tax credit rules, flags 55+ common dealership junk fees (such as VIN etching, paint protection, nitrogen tires, dealer prep, and market adjustments), calculates hidden loan interest on financed junk fees, and generates Polite, Firm, and Walk-Away counter-offer emails.

## Core Pages
- [CarQuoteCheck Home & OTD Auditor]({SITE_URL}/)
- [About & Audit Methodology]({SITE_URL}/about/)
- [Privacy Policy]({SITE_URL}/privacy-policy/)
- [Terms of Service]({SITE_URL}/terms-of-service/)
- [Contact & Report Outdated State Cap]({SITE_URL}/contact/)

## All 50 US States + DC Doc Fee & OTD Calculators
{chr(10).join(state_lines)}
"""
    write_text("llms.txt", llms)


def main() -> None:
    states_path = BASE_DIR / "data" / "states.json"
    with states_path.open("r", encoding="utf-8") as f:
        states = json.load(f)

    generate_favicon()
    generate_og_image()
    generate_headers()
    generate_homepage(states)
    generate_state_pages(states)
    generate_legal_and_trust_pages()
    generate_404()
    generate_crawl_and_ai_files(states)
    print(f"Build complete: generated site for {len(states)} jurisdictions using SITE_URL={SITE_URL}")


if __name__ == "__main__":
    main()
