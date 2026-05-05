# PURPOSE: Source of truth for all scheduled CI jobs; logs the daily-project-recap job schema
# CONSUMED BY: Maintainers, GitHub Actions UI
# DEPENDS ON: .github/workflows/daily-project-recap.yml
# TEST: none
# Scheduled Jobs

| Job name             | Schedule (UTC) | Purpose                                  |
|----------------------|----------------|------------------------------------------|
| `daily-project-recap`| `0 7 * * *`    | Posts a daily summary of active projects |

## daily-project-recap
- **Trigger:** `cron: "0 7 * * *"` (daily at 07:00 UTC)
- **Action:** Posts a message prompt requesting a daily summary of all active projects in this channel.
