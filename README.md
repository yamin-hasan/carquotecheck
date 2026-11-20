# CarQuoteCheck

A static, zero-backend US car dealership OTD and fee auditor built for GitHub and Cloudflare Pages.

## Build and package

1. Edit `SITE_URL` near the top of `build.py` when moving to a custom domain.
2. Replace `CONTACT_EMAIL` with a monitored mailbox.
3. Run `python build.py` from this directory.
4. The script regenerates the site, runs the pre-package audit, and writes `../carquotecheck-mvp.zip`.
5. Deploy the contents of this directory to Cloudflare Pages with no build command and the project root as the output directory.

## Architecture

- Plain HTML, CSS, and vanilla JavaScript. No framework, server, database, or backend API.
- State data: `data/states.json` (50 states + DC).
- Quote data stays in the browser. Saved quotes use local storage; share links use URL fragments.
- `apple-touch-icon.png` and `og-image.png` are generated with Pillow.

## Data limitations

State tax values are editable starting points and may exclude local tax or vehicle-specific rules. Doc-fee market figures are comparison benchmarks, not statutory limits. Several legal rule details remain explicitly unverified. Title and registration amounts are planning defaults. Verify the written buyer's order and current state guidance before relying on any number.

## Sources

- State fee and vehicle tax references: https://otdcheck.com/data/dealer-fees-and-car-sales-tax-by-state
- Dealer documentation fee market reference: https://caredge.com/guides/car-dealer-doc-fee-by-state
- FTC pricing transparency FAQ: https://www.ftc.gov/business-guidance/resources/automobile-industry-pricing-transparency-faqs

The state rules source is attributed in the About page. Third-party reference material remains subject to its own license and terms.
