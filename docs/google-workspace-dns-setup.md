# Google Workspace Email Setup — DNS Configuration

Step-by-step guide for setting up Google Workspace email on a domain managed through Squarespace DNS.

## Prerequisites

- Domain registered and DNS managed in Squarespace
- Google Workspace account created and domain verified
- Access to Squarespace DNS settings (Domains > DNS Settings)

---

## Step 1: Add MX Record

This tells email servers to route mail to Google.

In Squarespace DNS, add a **custom MX record**:

| Field    | Value              |
|----------|--------------------|
| Host     | `@`                |
| Type     | MX                 |
| Priority | `1`                |
| Data     | `smtp.google.com`  |
| TTL      | Lowest available   |

> If Squarespace auto-creates Google records via Domain Connect, verify the MX record appears under "Google records."

---

## Step 2: Add SPF Record

SPF authorizes Google to send email on behalf of your domain. Without this, outgoing emails will be rejected or land in spam.

Add a **custom TXT record**:

| Field | Value                                      |
|-------|--------------------------------------------|
| Host  | `@`                                        |
| Type  | TXT                                        |
| Data  | `v=spf1 include:_spf.google.com -all`      |
| TTL   | Lowest available                           |

> **Important:** If a default SPF record exists (e.g., `v=spf1 -all`), delete it first. Having two SPF records will cause failures.

---

## Step 3: Add DKIM Record

DKIM cryptographically signs outgoing emails, proving they haven't been tampered with.

### Generate the DKIM key:

1. Go to **Google Admin Console** → Apps → Google Workspace → Gmail
2. Click **Authenticate email**
3. Select your domain and click **Generate new record**
4. Copy the TXT record name and value

### Add the DKIM record in Squarespace:

| Field | Value                                          |
|-------|-------------------------------------------------|
| Host  | `google._domainkey`                             |
| Type  | TXT                                             |
| Data  | `v=DKIM1;k=rsa;p=<your-public-key>`            |
| TTL   | 1 hour                                          |

> Replace `<your-public-key>` with the full key from Google Admin Console.

### Activate DKIM:

After adding the DNS record, go back to Google Admin Console and click **Start authentication**. It may take up to 48 hours for DNS to propagate, but usually works within minutes.

---

## Step 4: Add DMARC Record

DMARC tells receiving servers what to do with emails that fail SPF/DKIM checks.

Add a **custom TXT record**:

| Field | Value                                                              |
|-------|--------------------------------------------------------------------|
| Host  | `_dmarc`                                                           |
| Type  | TXT                                                                |
| Data  | `v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com`               |
| TTL   | Lowest available                                                   |

> Replace `yourdomain.com` with your actual domain.

### DMARC Policy Options:

| Policy       | Behavior                                    | When to use                    |
|--------------|---------------------------------------------|--------------------------------|
| `p=none`     | Monitor only, no enforcement                | Initial setup / testing        |
| `p=quarantine` | Send failures to spam                     | After SPF + DKIM verified      |
| `p=reject`   | Block emails that fail checks entirely      | Full production lockdown       |

**Recommended:** Start with `p=none`, verify emails deliver correctly for a week, then tighten to `p=reject`.

---

## Step 5: Verify Setup

### Send a test email

Send an email from your new `@yourdomain.com` address to a personal Gmail account. Check that it arrives in the inbox (not spam).

### Check email headers

In the received email, click the three dots → **Show original**. Verify:

- **SPF:** PASS
- **DKIM:** PASS
- **DMARC:** PASS

### Online tools

- [Google Admin Toolbox MX Check](https://toolbox.googleapps.com/apps/checkmx/)
- [Mail Tester](https://www.mail-tester.com/) — send a test email and get a deliverability score

---

## Final DNS Summary

After setup, your custom DNS records should look like this:

| Host               | Type | Data                                         |
|--------------------|------|----------------------------------------------|
| `@`                | MX   | `smtp.google.com` (priority 1)               |
| `@`                | TXT  | `v=spf1 include:_spf.google.com -all`        |
| `google._domainkey`| TXT  | `v=DKIM1;k=rsa;p=<your-public-key>`          |
| `_dmarc`           | TXT  | `v=DMARC1; p=none; rua=mailto:dmarc@...`     |

---

## Troubleshooting

| Problem                        | Fix                                                        |
|--------------------------------|------------------------------------------------------------|
| Emails going to spam           | Check SPF and DKIM both show PASS in email headers         |
| "Could not verify domain"      | Wait up to 72 hours for DNS propagation, then retry        |
| Duplicate SPF records          | Delete the old `v=spf1 -all` before adding the Google one  |
| DKIM not authenticating        | Ensure no extra spaces in the TXT record data field        |
| Squarespace won't let you edit preset records | Delete the preset and recreate as a custom record |

---

## Notes

- Squarespace may auto-create some email security presets (`v=spf1 -all`, empty DKIM, strict DMARC). These get removed or need to be replaced when setting up Google Workspace.
- If using Domain Connect to activate Google, some records may be auto-configured under "Google records" section.
- TTL changes take effect after the previous TTL expires. Lower TTLs propagate faster.
