FROM oraclelinux:9-slim
LABEL maintainer="Team at Oracle"
LABEL description="OCI format to generate CD3 image"

########### Input Parameters for image creation ############
# UID of user on underlying OS. eg 503 for Mac
ARG USER_UID=1001
# Whether to download Jenkins as part of image creation
ARG USE_DEVOPS=YES
#############################################################

ARG USERNAME=cd3user
ARG USER_GID=$USER_UID
# Whether to download Provider as part of image creation
ARG DOWNLOAD_PROVIDER=YES
# TF Provider version
ARG TF_OCI_PROVIDER=6.15.0
ARG TF_NULL_PROVIDER=3.2.1

# Install sudo and other required dependencies
RUN microdnf install -y sudo && \
    groupadd --gid $USER_GID $USERNAME && \
    useradd --uid $USER_UID --gid $USER_GID -d /$USERNAME -m $USERNAME && \
    echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME && \
    mkdir -p /cd3user/tenancies && \
    chown -R $USERNAME:$USERNAME /cd3user/tenancies/ && \
    microdnf install -y vim && \
    microdnf install -y dnf && \
    microdnf install -y wget && \
    microdnf install -y unzip && \
    microdnf install -y graphviz && \
    echo 'alias vi="vim"' >> /etc/bashrc

USER $USERNAME
WORKDIR /cd3user/oci_tools/
COPY cd3_automation_toolkit cd3_automation_toolkit/
COPY othertools othertools/

WORKDIR /cd3user/

# Install Oracle Linux release and run shell script
RUN dnf install -y oraclelinux-release-el9 && \
    chown -R $USERNAME:$USERNAME /cd3user/ && \
    sed -i -e 's/\r$//' /cd3user/oci_tools/cd3_automation_toolkit/shell_script.sh && \
    bash -x /cd3user/oci_tools/cd3_automation_toolkit/shell_script.sh && \
    dnf clean all && \
    rm -rf /var/cache/dnf && \
    chmod -R 740 /cd3user/ && \
    chown -R cd3user:cd3user /cd3user/

# Download providers if requested
RUN if [ "$DOWNLOAD_PROVIDER" == "YES" ]; then \
    # OCI provider
    wget https://releases.hashicorp.com/terraform-provider-oci/${TF_OCI_PROVIDER}/terraform-provider-oci_${TF_OCI_PROVIDER}_linux_amd64.zip && \
    mkdir -p /cd3user/.terraform.d/plugins/registry.terraform.io/oracle/oci/${TF_OCI_PROVIDER}/linux_amd64 && \
    unzip terraform-provider-oci_${TF_OCI_PROVIDER}_linux_amd64.zip -d /cd3user/.terraform.d/plugins/registry.terraform.io/oracle/oci/${TF_OCI_PROVIDER}/linux_amd64 && \
    # Null provider
    wget https://releases.hashicorp.com/terraform-provider-null/${TF_NULL_PROVIDER}/terraform-provider-null_${TF_NULL_PROVIDER}_linux_amd64.zip && \
    mkdir -p /cd3user/.terraform.d/plugins/registry.terraform.io/hashicorp/null/${TF_NULL_PROVIDER}/linux_amd64 && \
    unzip terraform-provider-null_${TF_NULL_PROVIDER}_linux_amd64.zip -d /cd3user/.terraform.d/plugins/registry.terraform.io/hashicorp/null/${TF_NULL_PROVIDER}/linux_amd64 && \
    cp -r /cd3user/.terraform.d/plugins/registry.terraform.io /cd3user/.terraform.d/plugins/registry.opentofu.org && \
    chown -R cd3user:cd3user /cd3user/ && \
    rm -rf terraform-provider-null_${TF_NULL_PROVIDER}_linux_amd64.zip terraform-provider-oci_${TF_OCI_PROVIDER}_linux_amd64.zip ;\
    fi
