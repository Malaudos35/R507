# db.Dockerfile
# Utilise l'image officielle de MySQL depuis Docker Hub
FROM mysql:9.5

# Copie les scripts SQL dans le conteneur (optionnel, car le volume est déjà monté)
COPY ./my.conf /etc/mysql/conf.d/my.conf
# COPY ./sql/ /docker-entrypoint-initdb.d/

# Expose le port par défaut de MySQL
EXPOSE 3306

# Pas besoin de CMD, car l'image officielle démarre automatiquement le serveur MySQL