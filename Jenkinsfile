// Openshift project
OPENSHIFT_SERVICE_ACCOUNT = 'jenkins'
DOCKER_REPO_URL = 'docker-registry.default.svc.cluster.local:5000'
CI_NAMESPACE= env.CI_PIPELINE_NAMESPACE ?: 'ai-coe'
CI_TEST_NAMESPACE = env.CI_THOTH_TEST_NAMESPACE ?: 'ai-coe'

// Defaults for SCM operations
env.ghprbGhRepository = env.ghprbGhRepository ?: 'AICoE/thoth-dependency-monkey'
env.ghprbActualCommit = env.ghprbActualCommit ?: 'master'
// github-organization-plugin jobs are named as 'org/repo/branch'
// we don't want to assume that the github-organization job is at the top-level
// instead we get the total number of tokens (size) 
// and work back from the branch level Pipeline job where this would actually be run
// Note: that branch job is at -1 because Java uses zero-based indexing
tokens = "${env.JOB_NAME}".tokenize('/')
org = tokens[tokens.size()-3]
repo = tokens[tokens.size()-2]
branch = tokens[tokens.size()-1]

echo "${org} ${repo} ${branch}"

// If this PR does not include an image change, then use this tag
STABLE_LABEL = "stable"
tagMap = [:]

// IRC properties
IRC_NICK = "aicoe-bot"
IRC_CHANNEL = "#thoth-station"

properties(
    [
        buildDiscarder(logRotator(artifactDaysToKeepStr: '30', artifactNumToKeepStr: '', daysToKeepStr: '90', numToKeepStr: '')),
        disableConcurrentBuilds(),
    ]
)


library(identifier: "cico-pipeline-library@master",
        retriever: modernSCM([$class: 'GitSCMSource',
                              remote: "https://github.com/CentOS/cico-pipeline-library",
                              traits: [[$class: 'jenkins.plugins.git.traits.BranchDiscoveryTrait'],
                                       [$class: 'RefSpecsSCMSourceTrait',
                                        templates: [[value: '+refs/heads/*:refs/remotes/@{remote}/*']]]]])
                            )
library(identifier: "ci-pipeline@master",
        retriever: modernSCM([$class: 'GitSCMSource',
                              remote: "https://github.com/CentOS-PaaS-SIG/ci-pipeline",
                              traits: [[$class: 'jenkins.plugins.git.traits.BranchDiscoveryTrait'],
                                       [$class: 'RefSpecsSCMSourceTrait',
                                        templates: [[value: '+refs/heads/*:refs/remotes/@{remote}/*']]]]])
                            )
library(identifier: "ai-stacks-pipeline@master",
        retriever: modernSCM([$class: 'GitSCMSource',
                              remote: "https://github.com/AICoE/AI-Stacks-pipeline",
                              traits: [[$class: 'jenkins.plugins.git.traits.BranchDiscoveryTrait'],
                                       [$class: 'RefSpecsSCMSourceTrait',
                                        templates: [[value: '+refs/heads/*:refs/remotes/@{remote}/*']]]]])
                            )

pipeline {
    agent {
        kubernetes {
            cloud 'openshift'
            label 'thoth-master'
            serviceAccount OPENSHIFT_SERVICE_ACCOUNT
            containerTemplate {
                name 'jnlp'
                args '${computer.jnlpmac} ${computer.name}'
                image DOCKER_REPO_URL + '/'+ CI_NAMESPACE +'/jenkins-aicoe-slave:' + STABLE_LABEL
                ttyEnabled false
                command ''
            }
        }
    }
    stages {
        stage("Setup BuildConfig") {
            steps {
                script {                    
                    env.TAG = "test"
                    env.REF = "master"

                    // TODO check if this works with branches that are not included in a PR
                    if (env.BRANCH_NAME != 'master') {
                        env.TAG = env.BRANCH_NAME.replace("/", "-")

                        if (env.Tag.startsWith("PR")) {
                            env.REF = "refs/pull/${env.CHANGE_ID}/head"
                        } else {
                            env.REF = branch.replace("%2F", "/")
                        }
                    }

                    openshift.withCluster() {
                        openshift.withProject(CI_TEST_NAMESPACE) {
                            if (!openshift.selector("template/thoth-dependency-monkey-api-buildconfig").exists()) {
                                openshift.apply(readFile('openshift/buildConfig-template.yaml'))
                                echo "BuildConfig Template created!"
                            }

                            /* Process the template and return the Map of the result */
                            def model = openshift.process('thoth-dependency-monkey-api-buildconfig',
                                    "-p", 
                                    "IMAGE_STREAM_TAG=${env.TAG}",
                                    "GITHUB_URL=https://github.com/${org}/${repo}",
                                    "GITHUB_REF=${env.REF}")

                            echo "BuildConfig Model from Template"
                            echo "${model}"

                            echo "Updating BuildConfig from model..."
                            createdObjects = openshift.apply(model)
                        }
                    }
                }
            } // steps
        } // stage
        stage("Get Changelog") {
            steps {
                node('master') {
                    script {
                        env.changeLogStr = pipelineUtils.getChangeLogFromCurrentBuild()
                        echo env.changeLogStr
                    }
                    writeFile file: 'changelog.txt', text: env.changeLogStr
                    archiveArtifacts allowEmptyArchive: true, artifacts: 'changelog.txt'
                }
            }
        }
        stage("Build Container Images") {
//            parallel { // openshift client gets confused if I do communicate with Openshift in a parallel{} ?!
//                stage("API Service") {
                    steps {
                        echo "Building Thoth Dependency Monkey container image..."
                        script {
                            tagMap['dependency-monkey-api'] = aIStacksPipelineUtils.buildImageWithTag(CI_TEST_NAMESPACE, "dependency-monkey-api", "${env.TAG}")
//                        }

//                    }
//                }
//                stage("PyPI Validator") {
//                    steps {
                        echo "Building PyPI Validator container image..."
//                        script {
                            tagMap['pypi-validator'] = aIStacksPipelineUtils.buildImageWithTag(CI_TEST_NAMESPACE, "pypi-validator", "${env.TAG}")
                        }
                    }   
//                } 
//            }
        }
        stage("Deploy to Test") {
            steps {
                script {
                    // aIStacksPipelineUtils.redeployFromImageStreamTag(CI_TEST_NAMESPACE, "user-api", "${env.TAG}")
                    // redeploy from ImageStreamTag ${env.TAG}
                    openshift.withCluster() {
                        openshift.withProject(CI_TEST_NAMESPACE) {
                            echo "Creating test tag from user-api:${env.TAG}"

                            openshift.tag("${CI_TEST_NAMESPACE}/dependency-monkey-api:${env.TAG}", "${CI_TEST_NAMESPACE}/dependency-monkey-api:test")

                            /* Select the OpenShift DeploymentConfig object
                             * Initiate a `oc rollout latest` command
                             * Watch the status until the rollout is complete using the `oc`
                             * option `-w` to watch
                             */
                            def result = null

                            deploymentConfig = openshift.selector("dc", "dependency-monkey-api")
                            deploymentConfig.rollout().latest()

                            timeout(10) {
                                result = deploymentConfig.rollout().status("-w")
                            }

                            if (result.status != 0) {
                                error(result.err)
                            }
                        }
                    } // withCluster
                }
            }
        } // stage

/*
        stage("Testing") {
            failFast true
            parallel {
                stage("Functional Tests") {
                    steps {
                        sh 'echo noop pytest'
                        sh 'mkdir reports/ && touch reports/noop.xml'
                    }
                }
            }
        } */ 
        stage("Image Tag Report") {
            steps {
                script {
                    pipelineUtils.printLabelMap(tagMap)
                }
            }
        } // stage
        stage("Tag stable image") {
            steps {
                script {
                    // Tag ImageStreamTag ${env.TAG} as our new :stable
                    openshift.withCluster() {
                        openshift.withProject(CI_TEST_NAMESPACE) {
                            echo "Creating stable tag from dependency-monkey-api:${env.TAG}"

                            openshift.tag("${CI_TEST_NAMESPACE}/dependency-monkey-api:${env.TAG}", "${CI_TEST_NAMESPACE}/dependency-monkey-api:stable")
                        }
                    } // withCluster
                } // script
            } // steps
        } // stage
        stage("Trigger Promotion") {
            steps {
                script {
                    echo 'trigger promotion to Stage'
                } // script
            } // steps
        } // stage
    }
    post {
        always {
            script {
                // junit 'reports/*.xml'

                String prMsg = ""
                if (env.ghprbActualCommit != null && env.ghprbActualCommit != "master") {
                    prMsg = "(PR #${env.ghprbPullId} ${env.ghprbPullAuthorLogin})"
                }
                def message = "${JOB_NAME} ${prMsg} build #${BUILD_NUMBER}: ${currentBuild.currentResult}: ${BUILD_URL}"

                pipelineUtils.sendIRCNotification("${IRC_NICK}", IRC_CHANNEL, message)
                
            }
        }
        success {
            echo "All Systems GO!"
        }
        failure {
            script {
                def message = "${JOB_NAME} build #${BUILD_NUMBER}: ${currentBuild.currentResult}: ${BUILD_URL}"

//                mattermostSend channel: "#thoth-station", icon: 'https://avatars1.githubusercontent.com/u/33906690', message: "${message}"

                error "BREAK BREAK BREAK - build failed!"
            }
        }
    }
}
