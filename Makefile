.PHONY: install run-ingestor run-extractor run-validator run-enricher run-api run-ui \
       run-pipeline docker-up docker-down docker-rebuild \
       monitoring-up monitoring-down grafana-reset \
       test tf-init tf-plan tf-apply tf-destroy clean

COMPOSE = docker compose -f infra/docker-compose.yml

install:
	pip install -r requirements.txt

# ── Individual services (local) ──────────────────────────────────────────────

run-ingestor:
	python -m services.ingestor.main

run-extractor:
	python -m services.extractor.main

run-validator:
	python -m services.validator.main

run-enricher:
	python -m services.enricher.main

run-api:
	python -m services.api.main

run-ui:
	streamlit run services/ui/app.py

# ── Full pipeline (local) ────────────────────────────────────────────────────

run-pipeline: run-ingestor run-extractor run-validator run-enricher
	@echo "Pipeline complete"

# ── Docker ───────────────────────────────────────────────────────────────────

docker-up:
	$(COMPOSE) up --build

docker-down:
	$(COMPOSE) down -v

docker-rebuild:
	$(COMPOSE) build --no-cache
	$(COMPOSE) up

docker-rebuild-service:
	$(COMPOSE) build --no-cache $(SERVICE)
	$(COMPOSE) up -d $(SERVICE)

# ── Monitoring ───────────────────────────────────────────────────────────────

monitoring-up:
	$(COMPOSE) up -d api prometheus grafana
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana:    http://localhost:3000"

monitoring-down:
	$(COMPOSE) stop prometheus grafana

grafana-reset:
	$(COMPOSE) stop grafana
	docker volume ls -q --filter name=grafana | xargs -r docker volume rm
	$(COMPOSE) up -d grafana
	@echo "Grafana reset. Login: admin / changeme"

# ── Terraform ────────────────────────────────────────────────────────────────

tf-init:
	cd infra/terraform && terraform init

tf-plan:
	cd infra/terraform && terraform plan

tf-apply:
	cd infra/terraform && terraform apply

tf-destroy:
	cd infra/terraform && terraform destroy

# ── Testing ──────────────────────────────────────────────────────────────────

test:
	python -m pytest tests/ -v

# ── Utilities ────────────────────────────────────────────────────────────────

clean:
	$(COMPOSE) down -v
	rm -rf data/extracted_papers data/validated_papers data/enriched_papers
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned all data and volumes"

logs:
	$(COMPOSE) logs -f $(SERVICE)

status:
	$(COMPOSE) ps
