DC := docker compose --project-name turniere-match --project-directory .

runserver: build
	$(DC) up

build:
	docker build -t turniere-match .

shell:
	$(DC) exec match ash
