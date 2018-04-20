pipeline {
  agent any
  environment {
    if ( "$TAG_NAME" ) {
      LOOM_VERSION="$TAG_NAME"
    }
    else {
      LOOM_VERSION="${GIT_COMMIT.take(10)}"
    }
  }
  stages {
    stage('Build Docker image') {
      steps {
        sh 'docker build --build-arg LOOM_VERSION=${LOOM_VERSION} . -t loomengine/loom:${LOOM_VERSION}'
      }
    }
    stage('UnitTest') {
      steps {
        sh 'docker run loomengine/loom:${LOOM_VERSION} /loom/src/bin/run-unit-tests.sh'
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
      when { anyOf {
        branch 'master'
	branch 'development'
	expression { env.GIT_BRANCH =~ '^.*prerelease' }
	// If TAG_NAME is defined, this commit is tagged for release
	expression { env.TAG_NAME }
      }}
      steps {
        sh 'echo Run Integration Tests'
      }
    }
    stage('Info') {
      steps {
        sh 'env'
      }
    }
  }
}
