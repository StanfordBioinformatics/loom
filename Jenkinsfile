pipeline {
  agent any
  stages {
    stage('Build') {
      steps {
        sh 'echo "My branch is: ${env.BRANCH_NAME}"'
	sh 'virtualenv env'
        sh 'source env/bin/activate'
        sh 'build-tools/build-loom-packages.sh'
        sh 'build-tools/install-loom-packages.sh'
      }
    }
    stage('UnitTest') {
      steps {
        sh 'source env/bin/activate'
        sh 'bin/run-tests.sh'
      }
    }
  }
}
