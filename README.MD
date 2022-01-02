# Python Architecture Sample Project Implementation

This repository is used to track a sample implementation of the project described in the Python Architecture book "Architecture Patterns with Python".



## Change log:
* 2022-01-01: Implemented the UnitOfWork pattern to better represent atomic events. The UnitofWork Object opens and closes DB related transaction
within a ContextManager.
* 2021-12-31: Implemented decoupling strategies between the SQLAlchemy (SQLA) ORM and the Domain model. 
By default SQLA expires Object which are not tied to a Session anymore, rendering them useless outside of DB operations.
This implementation disables the "expire" workflow to enable further use after Session termination.

