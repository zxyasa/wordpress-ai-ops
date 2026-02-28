# SOP: Go-Live Testing & Rollback Plan

## Purpose
Ensure everything works before the restaurant starts taking real orders. Define rollback procedures if issues arise.

## Pre-Go-Live Checklist

### Square POS
- [ ] All menu items display correctly on POS
- [ ] Modifiers apply correctly and show on receipt
- [ ] Tax (GST 10%) calculates correctly
- [ ] Receipt prints with correct business name, address, ABN
- [ ] Kitchen printer receives orders with correct item details
- [ ] Cash payments process correctly
- [ ] Card payments process correctly (test with real card, refund after)
- [ ] Refund workflow tested

### Square Online Ordering
- [ ] Online ordering page loads on mobile and desktop
- [ ] All menu items and categories display correctly
- [ ] Pickup order — place, confirm, verify on POS
- [ ] Delivery order — place, confirm, verify zone and fee calculation
- [ ] Customer receives order confirmation email
- [ ] Order notification appears on POS within 30 seconds
- [ ] Custom domain resolves correctly (HTTPS, no certificate errors)
- [ ] Trading hours enforce correctly (ordering disabled outside hours)

### QR Table Ordering
- [ ] QR codes scan correctly on iPhone and Android
- [ ] Correct menu loads for QR orders
- [ ] Order is tagged with correct table number on POS
- [ ] Kitchen printer shows table number
- [ ] Payment flow works (if pay-at-order enabled)
- [ ] Multiple simultaneous QR orders don't conflict

### Integrations
- [ ] Google Business Profile — ordering link points to correct URL
- [ ] Facebook page — CTA button points to correct URL
- [ ] Website — all links to ordering page work

## Go-Live Procedure

1. **Confirm with client** — "We're ready to go live. Shall we proceed?"
2. **Enable live ordering** — switch from test mode to live
3. **Monitor first 5 orders** — watch for errors, delays, or missing items
4. **Check kitchen flow** — confirm printer and POS display are clear
5. **Send confirmation** — email client with:
   - Live ordering URL
   - QR code asset files (final versions)
   - Square Dashboard login reminder
   - Support contact details

## Rollback Plan

### If orders are failing:
1. Disable online ordering temporarily (Square Dashboard → Online → Pause)
2. QR ordering continues to work via POS if online is the issue
3. Diagnose: check internet, Square status page, printer connection
4. Fix and re-enable

### If menu is wrong:
1. Mark incorrect items as "hidden" in Square (do NOT delete)
2. Fix pricing/modifiers
3. Un-hide items

### If hardware fails:
1. Fall back to phone/tablet as POS (Square app on any device)
2. Kitchen orders can be relayed manually
3. Replace or reconnect printer

### Escalation
- Square support: 1800 760 137 (AU)
- Newcastle Hub support: (as per client agreement)
