DC := docker compose --project-name turniere-match --project-directory .

runserver: build
	$(DC) up

build:
	docker build -t turniere-match -f docker/production/Dockerfile .

shell:
	$(DC) exec match ash
