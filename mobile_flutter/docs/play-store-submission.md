# PayRails — Google Play Store Submission Guide

Paste-ready content + answers for submitting the PayRails Android app (TWA) to the
Google Play Store. App: **PayRails**, package **`com.onlinegbc.payrails`**, Play
account **`GBCai4org`**. The `.aab` is already uploaded to **Internal testing**;
the work below promotes it to **Production**.

> ⚠️ **Framing rule:** PayRails is a **minimum-viable-product demo — all
> transactions are simulated, no real money moves.** Keep this consistent across
> the Data safety form, Financial features declaration, and content rating, or you
> risk a finance-policy rejection.

---

## 0. Fastest path to "Listed" — do these in order

1. **Verify live logins** on `payrails.onlinegbc.com` (reviewers get locked out if these break):
   - Consumer: `consumer1@test.com` / `password123`
   - Merchant: `admin@acme.com` / `password123`
2. **Set up your app** checklist (Dashboard) — fill the declarations in §4.
3. **Main store listing** — paste §1 (name, descriptions, graphics).
4. **Data safety** — enter §2.
5. **App access** — enter §3 (reviewer logins).
6. **Content rating** — run questionnaire with §5 answers.
7. **Promote build** Internal → **Production** (§6). No rebuild needed — reuse the
   uploaded `.aab` since package id / icon / app name are unchanged.
8. **Start rollout to Production** → submit. First finance-app review typically
   takes a few days to ~1 week.

---

## 1. Store listing

**App name** (≤30 chars)
```
PayRails
```

**Short description** (≤80 chars)
```
Real-time payments over FedNow & RTP, plus a consumer wallet. MVP demo app.
```

**Full description** (≤4000 chars)
```
PayRails is a real-time payments demo that shows how money can move instantly between consumers and businesses across modern U.S. payment rails.

⚠️ Demonstration app: PayRails is a minimum-viable-product demo. All transactions are simulated and no real money moves. Please do not enter real bank account numbers or other sensitive financial information.

WHAT YOU CAN DO

• Consumer wallet — load a prepaid balance and pay merchants instantly.
• Pay by QR — scan a merchant or recipient code to start a payment in seconds.
• Business payments — merchants can send merchant-to-merchant (B2B) payments backed by a simple ledger.
• Choose your rail — route payments over FedNow, RTP, ACH, or card, with discounts on instant rails.
• Instant confirmation — see payments complete in real time with clear status updates.
• Built-in safety checks — unusual transactions are flagged before you confirm.

WHY MODERN RAILS

Instant payment networks like FedNow and RTP settle in seconds, around the clock. PayRails demonstrates how a single app can give consumers and businesses access to these rails with a clean, simple experience.

PRIVACY & SECURITY

All traffic is encrypted in transit (HTTPS/TLS). Passwords are stored hashed and sensitive fields are encrypted at rest. We never sell your personal information. You can request access to or deletion of your data at any time. See our privacy policy at https://payrails.onlinegbc.com/privacy.

PayRails is intended for users aged 18 and older.

Operated by GBC-ai4org (OnlineGBC). Questions: payrails-privacy@onlinegbc.com
```

**Release notes** (first Production release)
```
Initial release of PayRails — a real-time payments demo with a consumer wallet, pay-by-QR, merchant-to-merchant payments, and FedNow/RTP/ACH/card rail selection. All transactions are simulated.
```

**Listing metadata**
- Category: **Finance**
- Contact email: `payrails-privacy@onlinegbc.com`
- Website: `https://payrails.onlinegbc.com`
- Privacy policy: `https://payrails.onlinegbc.com/privacy`

**Graphics**
- App icon: 512×512 (required)
- Feature graphic: 1024×500 (already created — `mobile_flutter/...` feature graphic)
- Phone screenshots: min 2 (capture from the live PWA on a phone/emulator)

---

## 2. Data safety

> Mark every type **Collected = Yes, Shared = No.** Google Cloud hosts the app as a
> **processor acting on our behalf**, which is *not* "sharing" under Google's
> definitions.

**Top-level questions**

| Question | Answer |
|---|---|
| Does your app collect or share any required user data types? | **Yes** |
| Is all user data encrypted in transit? | **Yes** (HTTPS/TLS) |
| Do you provide a way for users to request data deletion? | **Yes** — `payrails-privacy@onlinegbc.com` |

**Data types** (Collected = Yes; Shared = No; Ephemeral = No)

| Category → Data type | Required/Optional | Purpose(s) |
|---|---|---|
| Personal info → Name | Required | App functionality, Account management |
| Personal info → Email address | Required | App functionality, Account management |
| Personal info → User IDs (account/merchant ID) | Required | App functionality, Account management |
| Financial info → User payment info (demo bank/payment details) | Optional | App functionality |
| Financial info → Purchase history (amounts, descriptions, recipients) | Required | App functionality |
| App info & performance → Diagnostics (request logs) | Required | App functionality, Fraud prevention/security |

**Do NOT declare:** Password (not a Data safety type), Location, Contacts, Photos,
Messages, Health — none collected.

**Security practices**
- Encrypted in transit: **Yes**
- Users can request data deletion: **Yes**
- Independent security review: **No** (optional — leave unchecked)
- Play Families Policy: **N/A** (18+)

**Judgment calls**
- *User payment info = Optional* assumes the demo never forces real account entry.
  If a flow requires payment details, switch to Required.
- *Diagnostics/logs* declared to be safe. If logs are truly ephemeral-security-only,
  you may omit that row.

---

## 3. App access (reviewer logins)

Select **"All or some functionality is restricted"** and add two instruction sets.

**Set 1 — Consumer (wallet payments)**
- Username: `consumer1@test.com`
- Password: `password123`
```
Open the app and tap Login. Enter the credentials above to sign in as a consumer.
This account has a pre-funded demo wallet (~$500). To test a payment, tap "Pay",
scan or enter a merchant ID (e.g. merchant-001), enter any amount and description,
then Confirm. All transactions are simulated — no real money moves.
```

**Set 2 — Merchant admin (business payments)**
- Username: `admin@acme.com`
- Password: `password123`
```
Log in with the credentials above to sign in as a merchant admin. Use "Send Payment"
to send a merchant-to-merchant (B2B) payment — enter a receiver merchant ID
(e.g. merchant-002), an amount, a description, optionally choose a rail, then send.
This is a simulated MVP demo; no real funds are transferred.
```

> Add to the notes: *"PayRails is a minimum-viable-product demo. All payments are
> simulated and no real money is moved."*

---

## 4. "Set up your app" declarations (Dashboard toggles)

| Item | Answer |
|---|---|
| Ads | **No ads** |
| Target audience & content | **18+** |
| Government apps | **No** |
| News apps | **No** |
| Financial features | Declare as a **simulated / no-real-money demo** (no real money movement). If it ever handles real funds, Google requires extra licensing docs — keep the "demo" framing consistent. |
| Privacy policy | `https://payrails.onlinegbc.com/privacy` |
| App access | See §3 |
| Data safety | See §2 |
| Content rating | See §5 |

---

## 5. Content rating questionnaire (IARC)

- **Email:** `payrails-privacy@onlinegbc.com`
- **App category:** **Utility, Productivity, Communication, or Other**
  (no dedicated Finance bucket exists; this is correct for a payments utility)

| Question | Answer |
|---|---|
| Violence (cartoon/fantasy/realistic) | No |
| Sexual content or nudity | No |
| Profanity or crude humor | No |
| Controlled substances references | No |
| Gambling (contains or simulates) | No |
| Real-money gambling | No |
| Users can interact / communicate with each other | No (no chat/messaging) |
| Users can share user-generated content | No |
| Shares user's physical location with other users | No |
| Purchase of digital goods | No (simulated; nothing actually purchased) |
| Other mature/sensitive content | No |

**Expected rating:** Everyone (ESRB) / PEGI 3 / equivalent.

**Judgment calls**
- *Users interact/communicate = No* — PayRails has no social/chat surface; sending
  a simulated payment isn't messaging. Answering Yes triggers moderation follow-ups.
- *Purchase digital goods = No* — keep consistent with the "demo, no real money"
  framing everywhere.

---

## 6. Promote build to Production

1. Install the **Internal testing** build on a real device via the opt-in link;
   confirm it launches full-screen (no browser URL bar = asset links verified ✓)
   and that login + a payment flow work.
2. Play Console → **Release → Production → Create new release**.
3. **Add from library** → select the `.aab` already uploaded to Internal testing
   (no rebuild needed — package/icon/name unchanged).
4. Fill **Release name** + **Release notes** (§1).
5. **Countries/regions** → select targets (e.g., United States).
6. **Review release** → resolve warnings → **Start rollout to Production**.
7. Watch **Publishing overview** for review status / policy requests.

---

## Reference — seeded demo accounts

From `backend/app/seed.py` (production runs `SEED_DATA=false`, so these exist only
because the Cloud SQL DB was seeded earlier — verify they still log in before submitting):

- Merchants: `admin@acme.com` (merchant-001), `admin@globex.com` (merchant-002), … / `password123`
- Consumers: `consumer1@test.com` (≈$500 wallet), `consumer2@test.com` / `password123`

## Reference — TWA rebuild (only if native fields change)

The app auto-updates with every web deploy. Only rebuild + re-upload a new `.aab`
if the **package id, icon, app name, or other native manifest fields** change:
`bubblewrap update && bubblewrap build` (keystore: `twa/android.keystore`, alias
`payrails` — gitignored; the user holds the only backup of the password).
