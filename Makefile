DC := docker compose --project-name turniere-match --project-directory .

runserver:
	$(DC) up

build:
	docker build -t turniere-match .
