pipeline {
  agent any
  stages {
    stage('Build Docker image') {
      steps {
        sh 'version=`echo ${GIT_COMMIT}|cut -c -10` && docker build --build-arg LOOM_VERSION=${version} . -t loomengine/loom:${version}'
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
