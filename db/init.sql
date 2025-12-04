CREATE DATABASE IF NOT EXISTS ordinateurs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ordinateurs;
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY 'bonjour';
GRANT ALL PRIVILEGES ON ordinateurs.* TO 'root'@'%';
FLUSH PRIVILEGES;
