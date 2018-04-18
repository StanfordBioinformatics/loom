pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        sh """
          echo "My branch is: ${env.BRANCH_NAME}" && \
	  virtualenv env && \
          . env/bin/activate && \
          build-tools/build-loom-packages.sh && \
          build-tools/install-loom-packages.sh
        """
      }
    }
    stage('UnitTest') {
      steps {
        sh """
          . env/bin/activate && \
          bin/run-tests.sh
        """
      }
    }
  }
}
