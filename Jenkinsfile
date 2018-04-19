pipeline {
  agent any
  environment {
    GIT_COMMIT_SHORT="${GIT_COMMIT.take(10)}"
  }
  stages {
    stage('Build Docker image') {
      steps {
        sh 'echo {$LOOM_VERSION}'
        sh 'docker build --build-arg LOOM_VERSION=${GIT_COMMIT_SHORT} . -t loomengine/loom:${GIT_COMMIT_SHORT}'
      }
    }
    stage('UnitTest') {
      steps {
        sh 'docker run loomengine/loom:${GIT_COMMIT_SHORT} /loom/src/bin/run-unit-tests.sh'
      }
    }
    stage('Push Docker image') {
      steps {
        // "docker push" requires that jenkins user first be authenticated
	// with "docker login".
	// Hashed docker credentials are written to ~/.docker/config.json
	// and remain valid as long as username and password are valid
        sh 'docker push loomengine/loom:${LOOM_VERSION}'
      }
    }
    stage('Integration Test') {
      when {
        anyOf {
	  branch 'master'
	  branch 'development'
	  branch '.*kins'
	  branch '.*prerelease'
	}
      }
      steps {
        sh 'echo Run Integration Tests'
      }
    }
  }
}