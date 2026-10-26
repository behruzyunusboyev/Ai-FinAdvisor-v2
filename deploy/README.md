# Production deployment preparation

The production stack keeps PostgreSQL and Redis private to the Compose network. Only Nginx publishes ports 80 and 443. It runs Alembic migrations before starting the API, serves the Next.js standalone build, and redirects HTTP to HTTPS.

## Before first start

1. On the server, install Docker Engine and the Docker Compose plugin. Copy the repository and create a server-only `.env` from `.env.example`; never commit that file. Use unique production credentials and a long random `SECRET_KEY`. Keep the database password URL-safe (`A-Z`, `a-z`, digits, `_`, `-`) because it is embedded in `DATABASE_URL` by Compose.
2. Set `ALLOWED_ORIGINS` to the exact HTTPS origin, for example `https://finadvisor.example.uz`. Set the approved tax and Payme values using the backend configuration notes. Leave Payme disabled until real merchant credentials and offer values are present.
3. Obtain a certificate for the domain using the server operator's approved certificate process. Put the matching full chain at `deploy/certs/fullchain.pem` and private key at `deploy/certs/privkey.pem`; restrict the private key to the deployment administrator and keep `deploy/certs` out of version control.
4. Edit `deploy/nginx/finadvisor.conf`: replace both occurrences of `finadvisor.example.uz` with the real domain. Confirm DNS points to this server and inbound TCP 80/443 are allowed.
5. Validate and start from the repository root:

   ```sh
   docker compose --env-file .env -f docker-compose.production.yml config
   docker compose --env-file .env -f docker-compose.production.yml up -d --build
   docker compose --env-file .env -f docker-compose.production.yml ps
   curl --fail https://YOUR_DOMAIN/health
   ```

Back up the PostgreSQL volume and certificate material using the server's approved backup process. Renew certificates before expiration and reload Nginx after renewal. The project does not automate domain registration, certificate issuance, firewall changes, or server provisioning; those require the target server and domain owner.
