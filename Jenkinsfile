pipeline {
  agent any
  stages {
    stage('Build Docker image') {
      steps {
        sh 'echo "Current branch is: ${env.BRANCH_NAME}'
        app = docker.build("loomengine/loom")
      }
    }
    stage('UnitTest') {
      steps {
        app.inside {
            sh '/loom/src/bin/run-tests.sh'
        }
      }
    }
  }
}
