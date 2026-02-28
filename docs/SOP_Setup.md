# SOP: Square Setup — Step-by-Step Checklist

## Purpose
Standardised setup process for Square POS, Online Ordering, and QR Table Ordering.

## Prerequisites
- [ ] Discovery call completed (SOP_Discovery.md)
- [ ] Client checklist received (menu, logo, hours, bank details)
- [ ] Client has confirmed go-ahead and payment terms

---

## Day 1–2: Base Setup

### Square Account
- [ ] Create Square account (or audit existing)
- [ ] Set business name, address, phone, email
- [ ] Connect bank account for payouts
- [ ] Set timezone to AEST (Australia/Sydney)
- [ ] Configure tax settings (10% GST)
- [ ] Set up service charges (if applicable)

### Menu Build
- [ ] Create item categories (mains, sides, drinks, desserts, specials)
- [ ] Add all menu items with:
  - [ ] Name
  - [ ] Description
  - [ ] Price
  - [ ] Photo (if provided)
  - [ ] SKU (optional)
- [ ] Create modifier sets (size, add-ons, dietary, cooking preference)
- [ ] Assign modifiers to relevant items
- [ ] Set item availability (if items vary by day/time)
- [ ] Review and QA — check every item with client

### Hardware Guidance
- [ ] Confirm hardware list with client
- [ ] Send purchase links (Square Store or Amazon AU)
- [ ] Document network requirements (Wi-Fi SSID, password, static IP if needed)

---

## Day 3: Square Online Ordering

- [ ] Enable Square Online
- [ ] Set ordering modes:
  - [ ] Pickup: yes/no, prep time, schedule
  - [ ] Delivery: yes/no, zones, fees, minimum order
  - [ ] Dine-in: yes/no (separate from QR)
- [ ] Configure trading hours for online ordering
- [ ] Set order throttling (if venue has kitchen capacity limits)
- [ ] Upload logo and hero image
- [ ] Set colour scheme to match branding
- [ ] Connect custom domain (or set up Square subdomain)
  - [ ] Add CNAME record in DNS
  - [ ] Verify domain connection
  - [ ] Enable SSL
- [ ] Test: place a test pickup order end-to-end
- [ ] Test: place a test delivery order end-to-end (if applicable)

---

## Day 4: QR Table Ordering

- [ ] Enable QR ordering in Square
- [ ] Create table groups (e.g., "Inside", "Outside", "Bar")
- [ ] Add tables to each group (Table 1, Table 2, etc.)
- [ ] Generate QR codes for each table
- [ ] Export print-ready QR assets:
  - [ ] PDF for table tents
  - [ ] PNG for stickers
  - [ ] Include venue branding on QR assets
- [ ] Configure QR order flow:
  - [ ] Menu items available via QR (may differ from counter menu)
  - [ ] Payment required at order or pay-at-counter
  - [ ] Tipping enabled/disabled
- [ ] Test: scan QR, place order, verify on POS and kitchen printer

---

## Day 5: Testing & Training

- [ ] Run full go-live checklist (see SOP_GoLive.md)
- [ ] Conduct staff training session (see SOP_Training.md)
- [ ] Hand over QR code assets to client
- [ ] Send login credentials summary to client (secure channel)

---

## Day 6–10: Adjustments & Go-Live

- [ ] Address feedback from training session
- [ ] Adjust menu items or modifiers as requested
- [ ] Fine-tune ordering hours or throttling
- [ ] Final go-live confirmation with client
- [ ] Switch page status from draft to published (if managing website)
- [ ] Monitor first 48 hours of live orders
- [ ] Send go-live confirmation email to client
