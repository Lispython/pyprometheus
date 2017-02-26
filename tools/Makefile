clean-containers:
	docker ps -q -f status=exited | xargs docker rm

build-images:
	@echo "Build docker images"
	docker-compose -f tools/compose-config.yml build # --force-rm


run-cmd:
	@echo "Execute command in docker"
	docker-compose -f tools/compose-config.yml run dev_pyprometheus $(DOCKER_CMD)

shell:
	@echo "Running shell in docker"
	docker-compose -f tools/compose-config.yml run dev_pyprometheus /bin/bash
