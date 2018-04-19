pipeline {
  agent any
  environment {
    LOOM_VERSION="${GIT_COMMIT.take(10)}"
  }
  stages {
    stage('Build Docker image') {
      steps {
        sh 'echo {$LOOM_VERSION}'
        sh 'docker build --build-arg LOOM_VERSION=${LOOM_VERSION} . -t loomengine/loom:${LOOM_VERSION} -t loomengine/loom:${GIT_BRANCH}'
      }
    }
    stage('UnitTest') {
      steps {
        sh 'docker run loomengine/loom /loom/src/bin/run-tests.sh'
      }
    }
    stage('Push Docker image') {
      steps {
        sh 'docker push loomengine/loom:${LOOM_VERSION}'
	sh 'docker push loomengine/loom:${GIT_BRANCH}'
      }
    }
  }
}
