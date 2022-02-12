all: down build up test

build:
	docker-compose build

up: build
	docker-compose up -d --build

down:
	docker-compose down --remove-orphans

test: up
	docker-compose run --rm --no-deps --entrypoint=pytest allocation tests/unit tests/integration tests/end_to_end

unit-tests:
	docker-compose run --rm --no-deps --entrypoint=pytest allocation tests/unit

integration-tests: up
	docker-compose run --rm --no-deps --entrypoint=pytest allocation tests/integration

end_to_end-tests: up
	docker-compose run --rm --no-deps --entrypoint=pytest allocation tests/end_to_end

logs:
	docker-compose logs --tail=25 -f allocation redis
