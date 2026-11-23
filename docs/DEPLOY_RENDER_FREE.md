# Deploy WARAQ Library Studio on Render Free

This guide creates a **public portfolio demo** at a Render `onrender.com` URL. It costs $0 on the Free instance, but it is not suitable for real library records because its SQLite file is temporary.

## Before you begin

- A GitHub account with access to `anasalsapi77-beep/Waraq-Library-Studio`.
- A free Render account.
- A new, unique manager password of at least 14 characters. Do not reuse your GitHub password or the local demo password.

## Create the service

1. Open [Render Dashboard](https://dashboard.render.com/).
2. Connect your GitHub account if Render asks for repository access.
3. Select **New → Blueprint**.
4. Choose `anasalsapi77-beep/Waraq-Library-Studio` and the `main` branch.
5. Render reads `render.yaml` from the repository. Confirm that the instance type is **Free** and the region is Singapore.
6. When Render asks for the secret `WARAQ_ADMIN_PASSWORD`, enter a new password of at least 14 characters. This value is not stored in GitHub.
7. Create the Blueprint and wait for the deployment to finish.

The service is configured with:
- Runtime: Python 3.13
- Build command: `python --version`
- Start command: `python main.py`
- Health check: `/health`
- Host: `0.0.0.0`
- Demo mode: disabled
- Manager username: `library-owner`
- SQLite file: `/tmp/waraq/library.db` (temporary)

## Open the app

1. In Render, open the new `waraq-library-studio` web service.
2. Copy its public `onrender.com` URL.
3. Visit the URL and sign in:
   - Username: `library-owner`
   - Password: the secret you entered during Blueprint creation.
4. From the manager dashboard, create a few sample books and member accounts for the portfolio demonstration.

Do not put your manager password in a GitHub file, README, issue, screenshot, or source-code commit.

## Free-plan limits you must understand

- The service sleeps after 15 minutes without inbound traffic.
- The next visitor can wait about one minute while it wakes up.
- The free web service has an ephemeral filesystem. SQLite changes are lost when the service spins down, restarts or redeploys.
- Free instance usage is limited to 750 hours per workspace per calendar month.
- Free web services cannot attach persistent disks.
- Render's free Postgres expires 30 days after creation, so it is not a permanent free database solution.

**Consequently, this free deployment is for a public portfolio demo only.** Do not use real member details, passwords, private records, or rely on the hosted copy to retain books and loan history. Your local SQLite database remains separate and is not uploaded by this deployment configuration.

## If the first deploy fails

Open the Render service's **Logs** and check that `WARAQ_ADMIN_PASSWORD` was supplied and is at least 14 characters. If the first deployment began before the secret was entered, add it under **Environment** and choose **Save, rebuild, and deploy**.

## Upgrade path

For a real shared library with durable records, move the app to a paid service with persistent storage or migrate the data layer to a durable managed PostgreSQL database. The free Render Blueprint intentionally does not attach paid storage.
