# Python Architecture Sample Project Implementation
[![Tests](https://github.com/yassineayadi/cosmic-python/actions/workflows/tests.yaml/badge.svg)](https://github.com/yassineayadi/cosmic-python/actions/workflows/tests.yaml)

This repository is used to track a sample implementation of the project described in the Python Architecture book "Architecture Patterns with Python".



## Change log:
* 2022-02-12: Decoupled database instance from application with separate Postgres container and default fallback to sqlite3.
* 2022-01-29: Implemented API documentation (Open API specifications) including a Swagger UI for user discovery.
* 2022-01-15: Implemented Marshmallow for deserialization/serialization of objects. Included thin wrapper to handle validation errors gracefully and surface error message to client.
* 2022-01-01: Implemented the UnitOfWork pattern to better represent atomic events. The UnitofWork Object opens and closes DB related transaction
within a ContextManager.
* 2021-12-31: Implemented decoupling strategies between the SQLAlchemy (SQLA) ORM and the Domain model.
By default SQLA expires Object which are not tied to a Session anymore, rendering them useless outside of DB operations.
This implementation disables the "expire" workflow to enable further use after Session termination.
