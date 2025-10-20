IMAGE_NAME = transcript_app
CONTAINER_NAME = transcript_app
PORT = 5000

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run -d -p $(PORT):$(PORT) --name $(CONTAINER_NAME) --env-file .env $(IMAGE_NAME)

stop:
	docker stop $(CONTAINER_NAME) || true

restart: stop
	docker start $(CONTAINER_NAME)

logs:
	docker logs -f $(CONTAINER_NAME)

shell:
	docker exec -it $(CONTAINER_NAME) /bin/bash

clean:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

rebuild: clean build run
	@echo "Container rebuilt and started!"

purge: clean
	docker rmi $(IMAGE_NAME) || true