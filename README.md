# nest-history

Collects and visualizes historical data from a Nest thermostat using the
Google Smart Device Management (SDM) API.

## Architecture

```
[Nest Thermostat]
      |
      | SDM API (every 30s)
      v
[collector] --> [VictoriaMetrics] --> [Grafana]
                                         ^
                                    [Caddy] (reverse proxy)
                                         ^
                                    port 80/443
```

All services run via Docker Compose on a GCP e2-micro VM (`us-west1-b`).
Infrastructure is managed with Terraform.

## Repository layout

```
collector/   Python collector service (Docker image)
deploy/      Docker Compose stack, Caddyfile, Grafana provisioning
infra/       Terraform config for GCP VM and firewall rules
```

## Prerequisites

- `gcloud` CLI, authenticated (`gcloud auth login` and `gcloud auth application-default login`)
- `terraform` (installed via HashiCorp apt repo)
- SSH key at `~/.ssh/nest_monitor` with access to the VM
- Docker and Docker Compose on the VM (already installed)

## Connecting to the VM

```bash
ssh -i ~/.ssh/nest_monitor kirk@8.229.167.176
```

If direct SSH is unavailable, fall back to:

```bash
gcloud compute ssh nest-monitor --project=nest-thermostat-history --zone=us-west1-b --ssh-key-file=~/.ssh/nest_monitor
```

## Deploying changes

### Collector code changes (`collector/`)

```bash
rsync -av -e "ssh -i ~/.ssh/nest_monitor" collector/ kirk@8.229.167.176:~/nest/collector/
ssh -i ~/.ssh/nest_monitor kirk@8.229.167.176 "cd ~/nest && docker compose up -d --build collector"
```

### Deploy config changes (`deploy/`)

Grafana provisioning, Caddyfile, or docker-compose.yml:

```bash
rsync -av -e "ssh -i ~/.ssh/nest_monitor" deploy/ kirk@8.229.167.176:~/nest/
ssh -i ~/.ssh/nest_monitor kirk@8.229.167.176 "cd ~/nest && docker compose up -d"
```

Restart a specific service after config changes:

```bash
ssh -i ~/.ssh/nest_monitor kirk@8.229.167.176 "docker restart nest-grafana-1"
```

### Infrastructure changes (`infra/`)

```bash
cd infra
terraform apply
```

## Checking logs

```bash
# All services
ssh -i ~/.ssh/nest_monitor kirk@8.229.167.176 "docker compose -f ~/nest/docker-compose.yml logs -f"

# Collector only
ssh -i ~/.ssh/nest_monitor kirk@8.229.167.176 "docker logs -f nest-collector-1"
```

## Secrets

Secrets are stored on the VM only and are never committed to this repo.

| File on VM             | Contents                                      |
|------------------------|-----------------------------------------------|
| `~/nest/.env`          | Grafana admin password                        |
| `~/nest/.env.collector`| SDM project ID, OAuth client ID/secret, refresh token |

To rotate the SDM refresh token, re-run the OAuth flow against
`https://nestservices.google.com/partnerconnections/{project-id}/auth`
and update `SDM_REFRESH_TOKEN` in `~/nest/.env.collector`, then restart
the collector.

## Enabling HTTPS

Edit `deploy/Caddyfile` — replace `:80` with your domain name:

```
your.domain.com {
    reverse_proxy grafana:3000
}
```

Deploy the change and Caddy will obtain a Let's Encrypt certificate automatically.
