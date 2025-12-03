CREATE DATABASE IF NOT EXISTS ordinateurs;
USE ordinateurs;

GRANT ALL PRIVILEGES ON ordinateurs.* TO 'root'@'%' IDENTIFIED BY 'bonjour';
FLUSH PRIVILEGES;

