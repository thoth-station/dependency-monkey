FROM registry.fedoraproject.org/fedora:27

LABEL io.k8s.description="Thoth Dependency Monkey Validator for Pypi" \
    io.k8s.display-name="Thoth: pypi validator" \
    io.openshift.tags="thoth,python,dependency_monkey,validator" \
    architecture=x86_64 \
    name="aicoe/pypi-validator" \
    vendor="Red Hat CTO Office - AI CoE" \
    license="GPLv3"

WORKDIR /opt/app-root/src

RUN mkdir /.cache && \
    pip3 install --upgrade pip && \
    pip3 install pip-tools thoth-analyzer && \
    chown 1001:1001 -R /opt/app-root/src /.cache

USER 1001

COPY validate /opt/app-root/src

ENTRYPOINT [ "/opt/app-root/src/validate" ]