pipeline {
  agent any
  stages {
    stage('Checkout') {
      steps {
        checkout([
          $class: 'GitSCM',
          branches: scm.branches,
          doGenerateSubmoduleConfigurations: scm.doGenerateSubmoduleConfigurations,
          extensions: scm.extensions + [[$class: 'CloneOption', noTags: false, reference: '', shallow: true]],
          submoduleCfg: [],
          userRemoteConfigs: scm.userRemoteConfigs
        ])
      }
    }
    stage('Build Docker image') {
      steps {
        sh 'docker build . -t loomengine/loom'
      }
    }
    stage('UnitTest') {
      steps {
        sh 'docker run loomengine/loom /loom/src/bin/run-tests.sh'
      }
    }
    stage('Push Docker image') {
      steps {
        sh 'env'
      }
    }
  }
}
