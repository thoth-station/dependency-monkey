# Thoth: Dependency Monkey

The "Dependency Monkey" is a service for validating of package dependencies within an application stack.

![The Dependency Monkey](graphics/dependency_monkey.png)

# Validation Request

# Valiation

The state of each Valiation is stored with it's corresponding Kubernetes Job. Validation results will be available for a certain amount of time (data retention period).

## Phases

* Pending: The Validation job has been accepted.

* Running: The Validation job has been bound to an executer (OpenShift node), and all of the containers have been created.

* Succeeded: All Containers of the Validation job have terminated successfully, and will not be restarted.

* Failed: All Containers in the Validation job have terminated, and at least one Container has terminated in failure.

* Unknown: For some reason the state of the Validation job could not be obtained.

# Deployment

```bash
oc create sa validation-job-runner
oc policy add-role-to-user view -z validation-job-runner
oc policy add-role-to-user edit -z validation-job-runner

oc create -f api-service-imageStream.yaml
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
