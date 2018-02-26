# Thoth: Dependency Monkey

The "Dependency Monkey" is a service for validating of package dependencies within an application stack.

![The Dependency Monkey](graphics/dependency_monkey.png)

# Validation Request

# Valiation

## Phases

* Pending: The Validation job has been accepted.

* Running: The Validation job has been bound to an executer (OpenShift node), and all of the containers have been created.

* Succeeded: All Containers of the Validation job have terminated successfully, and will not be restarted.

* Failed: All Containers in the Validation job have terminated, and at least one Container has terminated in failure.

* Unknown: For some reason the state of the Validation job could not be obtained.

# Badges

Travis-CI [![Build Status](https://travis-ci.org/goern/thoth-dependency-monkey.svg?branch=master)](https://travis-ci.org/goern/thoth-dependency-monkey)

## Testdrive

### Run MongoDB

`docker run --name mongodb --rm -ti --publish 27017:27017 -e MONGODB_USER=mongo -e MONGODB_PASSWORD=mongo -e MONGODB_DATABASE=dev -e MONGODB_ADMIN_PASSWORD=mongo centos/mongodb-32-centos7`

Start the API Service: `MONGODB_HOSTNAME=localhost DEBUG=True ./app.py`.

```bash
curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d '{"stack_specification":"tensorflow","ecosystem":"pypi"}' 'http://localhost:8080/api/v0alpha0/validations/'
```
