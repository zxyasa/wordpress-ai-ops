# SEO + Form Audit (2026-02-18)

## Scope
- Technical SEO baseline (front-end crawl)
- Lead capture form flow test (CF7 form id=400)

## SEO Audit Summary
- Pages checked: 62
- Total issues flagged: 115
- Highest-frequency issues:
  - Missing meta description on many pages
  - Some pages missing H1 (mostly Flatsome layout pages)
  - Title length out of preferred range on multiple pages
- Functional errors found:
  - `https://newcastlehub.info/cart/` -> HTTP 500
  - `https://newcastlehub.info/checkout/` -> HTTP 500
  - `https://newcastlehub.info/my-account/` -> HTTP 500

## Notes on scanner behavior
- Built-in `consistency-scan` returned zero findings on this site due REST edit-context constraints.
- A front-end crawl produced realistic findings and should be treated as source-of-truth for now.

## Form Flow Test (Free Newcastle Business Audit)
- Form id: `400`
- Endpoint tested: `POST /wp-json/contact-form-7/v1/contact-forms/400/feedback`
- Result: `status=mail_sent`
- API response message: `Thank you for your message. It has been sent.`

## Interpretation
- Form validation + submission path is working.
- If mailbox still receives nothing, the remaining issue is mail delivery (SMTP/DNS/spam routing), not CF7 form logic.

## Next Recommended Actions
1. SMTP deliverability hardening
- Ensure SMTP account is valid and not blocked.
- Verify SPF + DKIM + DMARC for sender domain.
- Keep FROM address on same authenticated domain.

2. Submission backup (no lead loss)
- Install/enable Flamingo (or equivalent) to store all CF7 submissions in WP DB.

3. Priority SEO fixes (phase 1)
- Core money pages first: `/`, `/services/`, `/about/`, `/contact/`, `/free-newcastle-business-audit/`, solution pages.
- Add/normalize meta descriptions and one clear H1 per page.

