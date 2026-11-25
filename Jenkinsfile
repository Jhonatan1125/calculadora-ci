pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
    }

    triggers {
        pollSCM('* * * * *')
    }

    environment {
        COMPOSE_PROJECT_NAME = 'calculadora-ci-test'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                sh '''
                    echo "=== Informacion del repositorio descargado ==="
                    git --version
                    git log -1 --oneline
                '''
            }
        }

        stage('Build') {
            steps {
                withCredentials([string(credentialsId: 'historial-api-key', variable: 'HISTORIAL_API_KEY')]) {
                    sh '''
                        set +x
                        cat <<EOF > .env
APP_PORT=8000
HISTORIAL_PORT=5001
HISTORIAL_SERVICE_URL=http://historial-api:5001
HISTORIAL_DATA_FILE=/data/historial.json
HISTORIAL_API_KEY=${HISTORIAL_API_KEY}
EOF
                        set -x
                        echo "=== Construyendo imagenes Docker de calculadora-api e historial-api ==="
                        docker compose -p "${COMPOSE_PROJECT_NAME}" build
                        docker compose -p "${COMPOSE_PROJECT_NAME}" config --images
                    '''
                }
            }
        }

        stage('Test') {
            steps {
                echo '=== 1. Ejecutando pruebas unitarias (pytest) en contenedor Docker efimero ==='
                sh '''
                    docker run --rm --volumes-from jenkins-ci -w "${WORKSPACE}" python:3.13.2-slim sh -c '
                        pip install --no-cache-dir -q pytest &&
                        pytest -v --junitxml=reporte-pruebas.xml
                        STATUS=$?
                        chmod 666 reporte-pruebas.xml 2>/dev/null || true
                        rm -rf .pytest_cache __pycache__
                        exit $STATUS
                    '
                '''

                echo '=== 2. Ejecutando prueba de integracion entre contenedores via Docker Compose ==='
                sh 'bash scripts/verificar_integracion.sh'
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'reporte-pruebas.xml'
            sh '''
                echo "=== Logs de los contenedores ==="
                docker compose -p "${COMPOSE_PROJECT_NAME}" logs --no-color || true
                echo "=== Deteniendo y limpiando contenedores, volumenes y .env temporal ==="
                docker compose -p "${COMPOSE_PROJECT_NAME}" down -v --remove-orphans || true
                rm -f .env reporte-pruebas.xml
            '''
        }
        success {
            echo 'BUILD EXITOSO: Ambas imagenes construidas, pruebas unitarias aprobadas y comunicacion entre calculadora-api e historial-api verificada.'
        }
        failure {
            echo 'BUILD FALLIDO: Se detecto un error en las pruebas o en la comunicacion entre servicios. Revisa Console Output y Test Result.'
        }
    }
}
