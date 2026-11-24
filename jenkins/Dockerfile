FROM docker:cli AS docker-cli

FROM jenkins/jenkins:lts-jdk21

USER root

# Copiar cliente Docker CLI y plugins oficiales (compose y buildx) desde docker:cli
COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker-cli /usr/local/libexec/docker/cli-plugins/ /usr/local/libexec/docker/cli-plugins/

# Evitar errores de 'dubious ownership' en repositorios montados con Git
RUN git config --system --add safe.directory '*'

USER jenkins

# Preinstalar plugins requeridos como codigo
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
