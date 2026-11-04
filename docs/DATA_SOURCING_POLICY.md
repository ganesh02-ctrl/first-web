# Data sourcing policy

1. **No invented records.** SSS ships with zero scholarships, and test fixtures use example.org URLs.
2. **Sources:** the National Scholarship Portal (scholarships.gov.in), state portals such as Karnataka SSP, university notices and other official government providers. As far as we know, NSP and SSP don't offer a public listing API, so SSS doesn't connect to them automatically. It also doesn't scrape portals or get around logins.
3. **Workflow:** an admin enters a record or imports a CSV. It starts **unverified** and unpublished. The admin opens the official source, compares every field, then clicks *mark verified*, which records the date and the admin. Only then can the record be published.
4. **Re-verification:** changing the deadline, links, amount or eligibility on a verified record sets it to *needs_review* and unpublishes it.
5. **Expiry:** once the closing date passes, the record shows as *expired*, and the daily job also stores that status.
6. **User reports:** students can flag wrong information, and admins handle these under Reports.

CSV columns: `title, provider_name, provider_type, scholarship_type, category, state, academic_year, description, benefits, amount_text, amount_max, application_open_date (YYYY-MM-DD), application_close_date, official_source_name, source_url, application_url, eligibility (JSON list), required_documents (JSON list)`.
