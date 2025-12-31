-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: data
-- ------------------------------------------------------
-- Server version	8.2.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `historico_acoes`
--

DROP TABLE IF EXISTS `historico_acoes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historico_acoes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `guardian_id` int NOT NULL,
  `data_evento` datetime DEFAULT NULL,
  `descricao` varchar(255) NOT NULL,
  `pontuacao` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `guardian_id` (`guardian_id`),
  CONSTRAINT `historico_acoes_ibfk_1` FOREIGN KEY (`guardian_id`) REFERENCES `guardians` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=52 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historico_acoes`
--

LOCK TABLES `historico_acoes` WRITE;
/*!40000 ALTER TABLE `historico_acoes` DISABLE KEYS */;
INSERT INTO `historico_acoes` VALUES (10,11,'2025-09-09 15:50:34','Completou o quiz \'Quiz Diário: Fundamentos de Senhas\' e ganhou 9 pontos.',9),(11,11,'2025-09-09 15:57:10','Conquistou a insígnia \'Batismo de Fogo\'!',0),(12,6,'2025-09-09 16:51:26','Completou o quiz \'Quiz Diário: Fundamentos de Senhas\' e ganhou 9 pontos.',9),(13,4,'2025-09-09 16:54:51','Completou o quiz \'Quiz Diário: Fundamentos de Senhas\' e ganhou 9 pontos.',9),(14,4,'2025-09-09 16:56:35','Completou o quiz \'Quiz Semanal: Golpes e Ameaças Comuns\' e ganhou 15 pontos.',15),(15,6,'2025-09-09 16:58:16','Completou o quiz \'Quiz Semanal: Golpes e Ameaças Comuns\' e ganhou 15 pontos.',15),(16,4,'2025-09-09 16:59:50','Conquistou a insígnia \'Batismo de Fogo\'!',0),(17,6,'2025-09-09 16:59:56','Conquistou a insígnia \'Batismo de Fogo\'!',0),(18,1,'2025-09-09 17:00:57','Completou o quiz \'Quiz Diário: Fundamentos de Senhas\' e ganhou 9 pontos.',9),(19,1,'2025-09-09 17:01:19','Conquistou a insígnia \'Batismo de Fogo\'!',0),(20,4,'2025-09-09 17:01:19','Completou o quiz \'Quiz Mensal: Phishing e Engenharia Social\' e ganhou 27 pontos.',27),(21,5,'2025-09-09 17:05:50','Completou o quiz \'Quiz Diário: Fundamentos de Senhas\' e ganhou 6 pontos.',6),(22,5,'2025-09-09 17:08:46','Completou o quiz \'Quiz Semanal: Golpes e Ameaças Comuns\' e ganhou 15 pontos.',15),(23,5,'2025-09-09 17:13:47','Completou o quiz \'Quiz Mensal: Phishing e Engenharia Social\' e ganhou 27 pontos.',27),(24,5,'2025-09-09 17:16:42','Conquistou a insígnia \'Batismo de Fogo\'!',0),(25,7,'2025-09-09 17:17:43','Completou o quiz \'Quiz Diário: Fundamentos de Senhas\' e ganhou 9 pontos.',9),(26,7,'2025-09-09 17:19:02','Conquistou a insígnia \'Batismo de Fogo\'!',0),(27,7,'2025-09-09 17:20:01','Completou o quiz \'Quiz Semanal: Golpes e Ameaças Comuns\' e ganhou 12 pontos.',12),(28,7,'2025-09-09 17:24:55','Completou o quiz \'Quiz Mensal: Phishing e Engenharia Social\' e ganhou 24 pontos.',24),(29,6,'2025-09-09 17:53:40','Completou o quiz \'Quiz Mensal: Phishing e Engenharia Social\' e ganhou 27 pontos.',27),(30,8,'2025-09-10 08:02:33','Completou o quiz \'Quiz Diário: Fundamentos de Senhas\' e ganhou 9 pontos.',9),(31,8,'2025-09-10 08:04:11','Completou o quiz \'Quiz Semanal: Golpes e Ameaças Comuns\' e ganhou 15 pontos.',15),(32,8,'2025-09-10 08:10:38','Completou o quiz \'Quiz Mensal: Phishing e Engenharia Social\' e ganhou 24 pontos.',24),(33,11,'2025-09-10 08:54:38','Completou o quiz \'Quiz Semanal: Golpes e Ameaças Comuns\' e ganhou 15 pontos.',15),(34,11,'2025-09-10 08:59:32','Completou o quiz \'Quiz Mensal: Phishing e Engenharia Social\' e ganhou 27 pontos. (+1 pts de bônus de ofensiva!)',28),(35,14,'2025-09-10 09:59:07','Completou o quiz \'Quiz Diário: Fundamentos de Senhas\' e ganhou 9 pontos.',9),(36,9,'2025-09-10 09:59:17','Completou o quiz \'Quiz Diário: Fundamentos de Senhas\' e ganhou 9 pontos.',9),(37,9,'2025-09-10 10:01:04','Completou o quiz \'Quiz Semanal: Golpes e Ameaças Comuns\' e ganhou 15 pontos.',15),(38,9,'2025-09-10 10:06:17','Completou o quiz \'Quiz Mensal: Phishing e Engenharia Social\' e ganhou 27 pontos.',27),(39,14,'2025-09-10 10:26:15','Completou o quiz \'Quiz Semanal: Golpes e Ameaças Comuns\' e ganhou 12 pontos.',12),(40,8,'2025-09-10 13:13:40','Conquistou a insígnia \'Batismo de Fogo\'!',0),(41,14,'2025-09-10 13:13:48','Conquistou a insígnia \'Batismo de Fogo\'!',0),(42,9,'2025-09-10 13:14:59','Conquistou a insígnia \'Batismo de Fogo\'!',0),(43,2,'2025-09-10 14:57:56','Completou o quiz \'Quiz Diário: Fundamentos de Senhas\' e ganhou 9 pontos.',9),(44,2,'2025-09-10 15:09:15','Completou o quiz \'Quiz Semanal: Golpes e Ameaças Comuns\' e ganhou 15 pontos.',15),(45,10,'2025-09-10 15:20:28','Completou o quiz \'Quiz Diário: Fundamentos de Senhas\' e ganhou 9 pontos.',9),(46,10,'2025-09-10 15:21:24','Conquistou a insígnia \'Batismo de Fogo\'!',0),(47,2,'2025-09-10 15:22:09','Conquistou a insígnia \'Batismo de Fogo\'!',0),(48,2,'2025-09-10 15:31:10','Completou o quiz \'Quiz Mensal: Phishing e Engenharia Social\' e ganhou 27 pontos.',27),(49,1,'2025-09-10 21:36:25','Completou o quiz \'Quiz Semanal: Golpes e Ameaças Comuns\' e ganhou 15 pontos.',15),(50,11,'2025-09-11 08:56:15','Completou o quiz \'Quiz Diário: Segurança de Redes\' e ganhou 9 pontos.',9),(51,8,'2025-09-11 09:40:45','Completou o quiz \'Quiz Diário: Segurança de Redes\' e ganhou 9 pontos.',9);
/*!40000 ALTER TABLE `historico_acoes` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-11 12:25:37
