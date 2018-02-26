# Thoth: Dependency Monkey

The "Dependency Monkey" is a service for validating of package dependencies within an application stack.

![The Dependency Monkey](graphics/dependency_monkey.png)

# Badges

Travis-CI [![Build Status](https://travis-ci.org/goern/thoth-dependency-monkey.svg?branch=master)](https://travis-ci.org/goern/thoth-dependency-monkey)

### Run MongoDB

`docker run --name mongodb --rm -ti --publish 27017:27017 -e MONGODB_USER=mongo -e MONGODB_PASSWORD=mongo -e MONGODB_DATABASE=dev -e MONGODB_ADMIN_PASSWORD=mongo centos/mongodb-32-centos7`
