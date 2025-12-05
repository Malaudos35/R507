FROM alpine

# Installer SSH et créer un utilisateur
RUN apk add --no-cache openssh && \
    adduser -D testuser && \
    echo "testuser:bonjour" | chpasswd && \
    mkdir -p /home/testuser/.ssh && \
    ssh-keygen -A

CMD ["/usr/sbin/sshd", "-D"]
