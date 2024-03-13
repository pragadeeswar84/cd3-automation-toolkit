/* Set the various stages of the build */
def tf_plan = "Changes"
pipeline {
    agent any
    options {
        ansiColor('xterm')
    }
    stages {
        stage('Terraform Destroy Plan') {
            when {
                expression { return env.GIT_BRANCH == 'origin/develop';}
            }

            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                script {
					def jobName = env.JOB_NAME
                    def parts = jobName.split('/')

                    // Assuming the job name format is <region_name>/job/<service_name>/job/job_name
                    def regionName = parts[1]
                    def serviceName = parts[2]

                    // Set environment variables for reuse in subsequent stages
                    env.Region = regionName
                    env.Service = serviceName
        	    
                    sh "cd \"${WORKSPACE}/${env.Region}/${env.Service}\" && terraform init -upgrade"
          	        //sh "cd \"${WORKSPACE}/${env.Region}/${env.Service}\" && terraform plan -destroy"


                    // Run Terraform plan
                    def terraformPlanOutput = sh(script: "cd \"${WORKSPACE}/${env.Region}/${env.Service}\"  && terraform plan -destroy", returnStdout: true).trim()

                    // Check if the plan contains any changes
                    if (terraformPlanOutput.contains('No changes.')) {
                        echo 'No changes in Terraform plan. Skipping further stages.'
                        tf_plan = "No Changes"
                    } else {
                        // If there are changes, proceed with applying the plan
                        echo "Proceeding with destroy. \n${terraformPlanOutput}"

                    }

                }
				}
            }
        }

        /** Approval for Terraform Apply **/
        stage('Get Approval') {
            when {
              allOf{
                expression {return env.GIT_BRANCH == 'origin/develop'; }
                expression {return tf_plan == "Changes" }
				expression {return currentBuild.result != "FAILURE" }
			  }
            }
            input {
                message "Do you want to perform terraform destroy?"

            }
            steps {
                echo "Approval for the Destroy Granted!"
            }
        }

        stage('Terraform Destroy') {
            when {
             allOf{
                expression {return env.GIT_BRANCH == 'origin/develop'; }
                expression {return tf_plan == "Changes" }
				expression {return currentBuild.result != "FAILURE" }
			  }
            }

            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
				script {
                    sh "cd \"${WORKSPACE}/${env.Region}/${env.Service}\" && terraform destroy --auto-approve"
                }
            }
		  }
        }


        /** Main branch commit to keep changes in Sync  **/
        stage('Commit To Main') {
            when {
                allOf {
                    expression { return env.GIT_BRANCH == 'origin/develop'; }
                    expression { return tf_plan == "Changes" }
                    expression { return currentBuild.result != "FAILURE" }
                }
            }
            steps {
                catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
                    script {
                        def buildDir = "${WORKSPACE}/${BUILD_NUMBER}"
                        // Create directory with build number
                        sh "mkdir -p ${buildDir}"

                        // Commit changes to the main branch
                        dir(buildDir) {
                            sh """
                                 git clone ${GIT_URL}
                                 cd \$(ls -d */|head -n 1)
                                 git checkout main
                                 ls -lrtha
                                 cd "${env.Region}/${env.Service}"
                                 git pull --no-edit origin main
                                 rm -f *.tfvars
                                 git rm *.tfvars
                                 git status
                                 git add --all .
                               """

                            def git_status = false
                            while (!git_status) {
                                // Execute the git commands using shell
                                def gitResult = sh(script: """
                                    cd "\$(ls -d */|head -n 1)"
                                    cd "${env.Region}/${env.Service}"
                                    git fetch origin main
                                    git merge origin/main
                                    git commit -m "Terraform destroy run for #build $BUILD_NUMBER - ${env.Region}/${env.Service}"

                                    git push --porcelain origin main
                                    """, returnStatus: true)

                                if (gitResult == 0) {
                                    git_status = true
                                } else {
                                    echo "Git operation failed, retrying...."
                                    sleep 3  // 3 seconds before retrying
                                }
                            }


                        }
                    }
                }
            }

            post {
                always {
                    // Delete the build directory and the temporary directory
                    deleteDir()
                }
            }
        }

    }
}
