pipeline {
    agent any
    enviroment {
        DOCKER_IMAGE = 'bitget-api'
        DOCKER_REGISRY = 'docker-registry.hub'
        DOCKER_CREDENTIALS = 'docker-credentials'
    }

    stages {
        stage('Code checkout') {
            steps {
                echo 'Checking out the code..'
            }
        }

        stage('Static code analysis') {
            echo 'Analysing the static code throught SonarQube'
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing dependencie..'
            }
        }

        stage('Run Linting') {
            steps {
                echo 'Runing Linting..'
            }
        }
        
        stage('Run Unit Tests') {
            steps {
                echo 'Runing Unit tests..'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'
            }
        }

        stage('Push Docker Image') {
            echo 'pushing docker image..'
        }

        stage('Deploy to Dev Environment') {
            echo ''
        }
    }

    post {
        success{
            echo 'Pipeline executed sucessfully!'
        }
        failiture {
            echo 'Pipeline failed'
        }
    }
}