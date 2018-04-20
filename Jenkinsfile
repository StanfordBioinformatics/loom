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
//    c. Build strategies:
//       - Regular branches
//       - Tags
//    d. Configure other settings as needed
// 6. Add deployment settings in ~jenkins/.loom-deploy-settings
//    a. Settings in ~jenkins/.loom-deploy-settings/loom.conf
//    b. Resources in ~jenkins/.loom-deploy-settings/resources/

pipeline {
  agent any
  environment {
    // If this is a tagged build, version will be TAG_NAME.
    // Otherwise take version from git commit
    LOOM_VERSION="${ TAG_NAME ? TAG_NAME : GIT_COMMIT.take(10) }"
    LOOM_DEPLOY_SETTINGS_DIR=
  }
  stages {
    stage('Build Docker Image') {
      steps {
        sh 'docker build --build-arg LOOM_VERSION=${LOOM_VERSION} . -t loomengine/loom:${LOOM_VERSION}'
      }
    }
    stage('Unit Tests') {
      steps {
        sh 'docker run loomengine/loom:${LOOM_VERSION} /loom/src/bin/run-unit-tests.sh'
      }
    }
    stage('Push Docker Image') {
      steps {
        // "docker push" requires that jenkins user first be authenticated
	// with "docker login" on host OS.
	// Hashed docker credentials are written to ~/.docker/config.json
	// and remain valid as long as username and password are valid
        sh 'docker push loomengine/loom:${LOOM_VERSION}'
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
	sh 'if [ ! -f ~/.loom-deploy-settings/ ]; then echo ERROR Loom deployment settings not found; fi'
	sh mkdir $WORKSPACE/.loom
	sh 'docker run -v ${HOME}/.loom-deploy-settings/:/deploy-settings/ -v $WORKSPACE/.loom/:/root/.loom/ loomengine/loom:${LOOM_VERSION} loom server start -s /deploy-settings/loom.conf -r /deploy-settings/resources/'
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
        sh 'docker run -v `$WORKSPACE/.loom/:/root/.loom/ loomengine/loom:${LOOM_VERSION} loom test integration'
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
}

postBuild {
  always ('Cleanup') {
    //sh 'docker run -v `$WORKSPACE/.loom/:/root/.loom/ loomengine/loom:${LOOM_VERSION} loom server delete'
    sh 'echo Cleanup'
  }
}
