# Thoth: Dependency Monkey

The "Dependency Monkey" is a service for validating of package dependencies within an application stack.

![The Dependency Monkey](graphics/dependency_monkey.png)


# Software Stacks

By Software Stack we mean any set of packages that is requires to provide the functions requires by your software. A software stack is valid, if we can create a set of direct acyclic graphs, that contains all packages requires by the software stack. These packages may include version specifications.

# Validation

A Validation is the task of evaluation if a given software stack specification could be resolved into a set of graphs. The resolution algorithm or tool may be specific to each ecosystem the software packages come from.

# An Example

Right now the dependency monkey is capable of validating Python requirements/software stacks: if you ask him to 'validate pandas and numpy and six' it will tell you if this software stack is valid or not. The API will also return a resolved and locked dependency list, always defaulting to the latest version of each package.

Let's take a look at the workflow: first of all we request a new Validation, note that package specifications are delimited by newlines!

```bash
curl -X POST --header 'Content-Type: application/json' \
     --header 'Accept: application/json' \
     -d '{"ecosystem":"pypi","stack_specification":"pandas\\nnumpy>=1.11.0"}' \
     http://api-service-thoth-dev.1d35.starter-us-east-1.openshiftapps.com/api/v0alpha0/validations/
```

This will return an (pretty empty) object:

```javascript
Validation {
 stack_specification (string): Specification of the Software Stack ,
 valid (boolean, optional): This indicates that the Validation is valid ,
 raw_log (string, optional): This is the raw log of the Validation job ,
 ecosystem (string): Ecosystem the stack specification will be validated,
 id (string): The Validation unique identifier ,
 phase (string): Phase of the Validation job: [pending, running, succeeded, failed]
}
```

Take note of the ID, we will need it for subsequent requests. You will also see that 'valid' is still null, as the Validation has not finished. In the background an OpenShift Job is scheduled to use a specific image to validate the software stack.

As we are keen what the progress is, we can use

```bash
curl -X GET --header 'Accept: application/json' \
     http://api-service-thoth-dev.1d35.starter-us-east-1.openshiftapps.com/api/v0alpha0/validations/9b76ecc4-4899-41aa-b3a6-e8d2325dbac8
```

After some time you should see that the phase of the Validation Job reads 'succeeded', which means Dependency Monkey has come to a conclusion: the software stack you requests is either valid or not. Use the curl command from about to get the final result.

# API

Right now the Validation API is at version v0alpha0, please find an [OpenAPI definition](swagger.json) within this repository.

# Validation Request

This section details what the attributes of a Validation mean.

# Valiation

The state of each Valiation is stored with it's corresponding Kubernetes Job. Validation results will be available for a certain amount of time (data retention period).

## Phases

* Pending: The Validation job has been accepted.

* Running: The Validation job has been bound to an executer (OpenShift node), and all of the containers have been created.

* Succeeded: All Containers of the Validation job have terminated successfully, and will not be restarted.

* Failed: All Containers in the Validation job have terminated, and at least one Container has terminated in failure.

* Unknown: For some reason the state of the Validation job could not be obtained.

## Validator Interface

Each Validation is carried out in its specific ecosystem, so per ecosystem there is a Validator, they get run as OpenShift Jobs, therefore they are wrapped up in a container image. Validator container images are located in [images/](images/).

All Validators expect two environment variables: `ECOSYSTEM` and `STACK_SPECIFICATION`, they should be injected into a running container. For convenience all Validators should use the entrypoint `validate`.

# Deployment

```bash
oc new-project thoth-dev

oc create sa validation-job-runner
oc policy add-role-to-user view -z validation-job-runner
oc policy add-role-to-user edit -z validation-job-runner

oc create -f api-service-buildConfig.yaml

oc process -f api-service-template.yaml | oc create -f -
```

# Continous Integration

A CI pipeline is hosted on CentOS CI infrastructure: [thoth-dependency-monkey](https://jenkins-ai-coe.apps.ci.centos.org/blue/organizations/jenkins/thoth-dependency-monkey/branches)

## Testdrive

Start the API Service: `DEBUG=True ./app.py`.

```bash
curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d '{"stack_specification":"pandas","ecosystem":"pypi"}' 'http://localhost:8080/api/v0alpha0/validations/'

curl -X GET --header 'Accept: application/json' 'http://localhost:8080/api/v0alpha0/validations/<ID>'
```
