pipeline {
  agent any
  stages {
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
