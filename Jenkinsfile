#!groovy

node {
  stage('Debug') {
    sh 'env'
    checkout scm
    sh 'env'
  }
}

/*
node {
  stage('Checkout') {
    checkout scm
    env.LOOM_VERSION="${ env.TAG_NAME ? env.TAG_NAME : env.GIT_COMMIT.take(10) }"
  }
  stage('Build Docker Image') {
    sh 'docker build --build-arg LOOM_VERSION=${LOOM_VERSION} . -t loomengine/loom:${LOOM_VERSION}'
  }
  stage('UnitTest') {
    sh 'docker run loomengine/loom:${LOOM_VERSION} /loom/src/bin/run-unit-tests.sh'
    }
  stage('Push Docker image') {
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
    stage('Release') {
      when { 
        // Release if tagged
        expression { env.TAG_NAME }
      }
      timeout(time: 3 units: 'MINUTES') {
        def approveRelease = input id: 'approveRelease',
                              message: 'Publish a new Loom release?'
      }
      steps {
        sh 'echo Deploying now'
      }
    }
  }
}
*/
