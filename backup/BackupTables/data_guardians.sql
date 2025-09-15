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
-- Table structure for table `guardians`
--

DROP TABLE IF EXISTS `guardians`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `guardians` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nickname` varchar(100) DEFAULT NULL,
  `is_anonymous` tinyint(1) NOT NULL,
  `featured_insignia_id` int DEFAULT NULL,
  `name_color` varchar(7) DEFAULT NULL,
  `user_id` int NOT NULL,
  `nome` varchar(100) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `grupo` varchar(100) DEFAULT NULL,
  `is_admin` tinyint(1) DEFAULT NULL,
  `score_atual` int DEFAULT NULL,
  `opt_in_real_name_ranking` tinyint(1) DEFAULT NULL,
  `departamento_id` int DEFAULT NULL,
  `departamento_nome` varchar(100) DEFAULT NULL,
  `departamento_score` int DEFAULT NULL,
  `ultima_atividade` datetime DEFAULT NULL,
  `avatar_url` varchar(255) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  `nivel_id` int DEFAULT NULL,
  `current_streak` int DEFAULT NULL,
  `last_streak_date` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `email` (`email`),
  KEY `featured_insignia_id` (`featured_insignia_id`),
  KEY `nivel_id` (`nivel_id`),
  CONSTRAINT `guardians_ibfk_1` FOREIGN KEY (`featured_insignia_id`) REFERENCES `insignias` (`id`),
  CONSTRAINT `guardians_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `usuarios` (`id`),
  CONSTRAINT `guardians_ibfk_3` FOREIGN KEY (`nivel_id`) REFERENCES `niveis_seguranca` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `guardians`
--

LOCK TABLES `guardians` WRITE;
/*!40000 ALTER TABLE `guardians` DISABLE KEYS */;
INSERT INTO `guardians` VALUES (1,'dandan',0,5,'#39FF14',5,'dneto','dneto@comnect.com.br','Suporte',1,24,0,10,'TI',0,'2025-08-28 14:54:26','https://meu-servidor.com/avatars/dneto.png',NULL,'2025-09-10 21:36:25',1,2,'2025-09-10'),(2,'lolegario',0,NULL,'#39FF14',2,'lolegario','luciano@comnect.com.br','TI',1,51,0,10,'TI',0,'2025-08-28 15:12:57','https://meu-servidor.com/avatars/luciano.png',NULL,'2025-09-10 15:31:10',1,1,'2025-09-10'),(4,'Fábio Silva',0,5,'#FFD700',3,'Fabio Silva','fsilva@comnect.com.br','Gestor TI',0,51,1,3,'TI',300,'2025-08-31 14:30:00','https://example.com/avatar.jpg','2025-09-01 12:43:31','2025-09-09 17:06:25',1,1,'2025-09-09'),(5,'',0,5,'#C0C0C0',7,'Gustavo Maciel','gmaciel@comnect.com.br',NULL,0,48,1,NULL,'TI',0,NULL,NULL,'2025-09-04 14:41:27','2025-09-09 17:16:58',1,1,'2025-09-09'),(6,'lkaizer',0,5,'#00BFFF',8,'Lucas Kaizer','lkaizer@comnect.com.br',NULL,0,51,0,NULL,'TI',0,NULL,NULL,'2025-09-04 17:20:04','2025-09-09 17:53:40',1,1,'2025-09-09'),(7,'Raysa Melo',0,NULL,'#FF00FF',12,'Raysa Melo','gmelo@comnect.com.br',NULL,0,45,0,NULL,'TI',0,NULL,NULL,'2025-09-04 17:21:12','2025-09-09 17:24:55',1,1,'2025-09-09'),(8,'MatheusM2',0,NULL,'#00BFFF',9,'Matheus Silva','msilva@comnect.com.br',NULL,0,57,0,NULL,'TI',0,NULL,NULL,'2025-09-05 06:56:04','2025-09-11 09:40:45',1,2,'2025-09-11'),(9,'',0,NULL,'#CD7F32',14,'Eduardo Pinheiro','epinheiro@comnect.com.br',NULL,0,51,1,NULL,'TI',0,NULL,NULL,'2025-09-05 09:45:50','2025-09-10 10:34:56',1,1,'2025-09-10'),(10,NULL,0,NULL,NULL,15,'Chrysthyanne Rodrigues','crodrigues@comnect.com.br',NULL,0,9,1,NULL,'TI',0,NULL,NULL,'2025-09-05 16:16:43','2025-09-10 15:20:28',1,1,'2025-09-10'),(11,'fzanella',0,5,'#FF00FF',16,'Fernando Zanella','fzanella@comnect.com.br',NULL,1,61,0,NULL,'TI',0,NULL,NULL,'2025-09-05 16:20:39','2025-09-11 08:58:59',1,3,'2025-09-11'),(14,NULL,0,NULL,NULL,6,'Renato Ragga','rragga@comnect.com.br',NULL,0,21,1,NULL,'TI',0,NULL,NULL,'2025-09-09 07:20:35','2025-09-10 10:26:15',1,1,'2025-09-10'),(15,NULL,0,NULL,NULL,13,'Suporte','suporte@comnect.com.br',NULL,0,0,0,NULL,'BOT',0,NULL,NULL,'2025-09-10 06:45:22','2025-09-10 13:16:28',1,0,NULL);
/*!40000 ALTER TABLE `guardians` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-11 12:25:34
