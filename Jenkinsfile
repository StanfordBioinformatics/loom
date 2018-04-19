node {
  def app

  stage('Clone repo') {
    checkout scm
  }

  stage('Build docker image') {
    echo "Current branch is: ${env.BRANCH_NAME}
    app = docker.build("loomengine/loom")
  }
  
  stage('UnitTest') {
    app.inside {
      sh '/loom/src/bin/run-tests.sh'
    }
  }
}
