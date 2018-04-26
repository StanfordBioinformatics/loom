#!groovy

// Jenkins configuration
// 1. Enable Jenkins Pipeline plugins
// 2. Enable Basic Branch Build Strategies Plugin
// 3. Enable Git Parameters Plugin
// 4. Create a MultiBranch Pipeline tracking git repo, and configure git repo
//    to trigger to Jenkins web-hooks
// 5. Configure GitHub settings:
//    a. Docker credentials should be saved in Jenkins and applied to "GitHub"
//       plugin settings
//    b. Advanced clone behaviors: Fetch tags
//    c. Clean before checkout
//    d. Build strategies:
//       - Regular branches
//       - Tags
//    e. Configure other settings as needed
// 6. Add deployment settings in ~jenkins/.loom-deploy-settings
//    a. Settings in ~jenkins/.loom-deploy-settings/loom.conf
//    b. Resources in ~jenkins/.loom-deploy-settings/resources/
// 7. Add pypi credentials in ~jenkins/.pypirc
// 8. In Jenkins, add credentials for loom admin username and password to be
//    set on new Loom servers. Use credentials id "loom-admin"

pipeline {
  agent any
  environment {
    // If this is a tagged build, version will be TAG_NAME.
    // Otherwise take version from git commit
    VERSION="${ TAG_NAME ? TAG_NAME : GIT_COMMIT.take(10) }"
    LOOM_SETTINGS_HOME="${WORKSPACE}/.loom/"
    LOOM_SERVER_NAME="${BUILD_TAG}"
    GOOGLE_APPLICATION_CREDENTIALS="${HOME}/.loom-deploy-settings/resources/gcp-service-account-key.json"
  }
  stages {
    stage('Build Docker Image') {
      steps {
        sh 'docker build --build-arg LOOM_VERSION=${VERSION} . -t loomengine/loom:${VERSION}'
        script {
	  if (!env.TAG_NAME) {
            sh 'docker build --build-arg LOOM_VERSION=${VERSION} . -t loomengine/loom:${GIT_BRANCH}'
          }
        }
      }
    }
    stage('Unit Tests') {
      steps {
        sh 'docker run loomengine/loom:${VERSION} /loom/src/bin/run-unit-tests.sh'
      }
    }
    stage('Push Docker Image') {
      steps {
        // "docker push" requires that jenkins user first be authenticated
	// with "docker login" on host OS.
	// Hashed docker credentials are written to ~/.docker/config.json
	// and remain valid as long as username and password are valid
        sh 'docker push loomengine/loom:${VERSION}'
	script {
          if (!env.TAG_NAME) {
            sh 'docker push loomengine/loom:${GIT_BRANCH}'
          }
        }
      }
    }
    stage('Deploy Test Environment') {
      /*
      when { anyOf {
        branch 'master'
	branch 'development'
	expression { env.GIT_BRANCH =~ '^.*prerelease' }
	// If TAG_NAME is defined, this commit is tagged for release
	expression { env.TAG_NAME }
      }}
      */
      steps {
        // Install loom client locally
        sh 'virtualenv env'
        sh 'build-tools/set-version.sh ${VERSION}'
        sh '. env/bin/activate && pip install -r build-tools/requirements.pip'
        sh '. env/bin/activate && pip install -r build-tools/requirements-dev.pip'
        sh '. env/bin/activate && build-tools/build-loom-packages.sh'
	sh '. env/bin/activate && build-tools/install-loom-packages.sh'
        sh 'if [ ! -f ~/.loom-deploy-settings/loom.conf ]; then echo ERROR Loom deployment settings not found; fi'
	sh 'mkdir $WORKSPACE/.loom'
        withCredentials([[$class: 'UsernamePasswordMultiBinding', credentialsId:'loom-admin',
          usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD']
        ]) {
	  script {
	    loomServerStarted = true
	  }
          sh '. env/bin/activate && loom server start -s ${HOME}/.loom-deploy-settings/loom.conf -r ${HOME}/.loom-deploy-settings/resources/ -e LOOM_ADMIN_USERNAME=${USERNAME} -e LOOM_ADMIN_PASSWORD=${PASSWORD}'
          sh '. env/bin/activate && loom auth login $USERNAME -p $PASSWORD'
	}
      }
    }
    stage('Integration Tests') {
      /*
      when { anyOf {
        branch 'master'
	branch 'development'
	expression { env.GIT_BRANCH =~ '^.*prerelease' }
	// If TAG_NAME is defined, this commit is tagged for release
	expression { env.TAG_NAME }
      }}
      */
      steps {
        sh '. env/bin/activate && loom test integration --timeout 900'
      }
    }
    stage('Publish Release') {
      when {
        expression { env.TAG_NAME }
      }
      steps {
        sh 'echo Publish Release'
      }
    }
  }
  stage('Release to PyPi') {
    when {
      expression { env.TAG_NAME }
    }
    sh '. env/bin/activate && build-tools/pypi-release.sh'
  }
  post {
    always ('Cleanup') {
      script {
        if (loomServerStarted) {
          sh '. env/bin/activate && loom server delete --confirm-server-name ${LOOM_SERVER_NAME}'
	}
      }
    }
    success {
      emailext (
        subject: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
        body: """SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':
          Check console output at ${env.BUILD_URL}'""",
        recipientProviders: [[$class: 'DevelopersRecipientProvider']]
      )
    }
    failure {
      emailext (
        subject: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
        body: """FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':
          Check console output at ${env.BUILD_URL}""",
        recipientProviders: [[$class: 'DevelopersRecipientProvider']]
      )
    }
  }
}
