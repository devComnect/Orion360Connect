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
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(20) NOT NULL,
  `password` varchar(200) NOT NULL,
  `is_admin` tinyint(1) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT (now()),
  `email` varchar(120) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `is_nivel2` int DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'admin','scrypt:32768:8:1$Ec2LAwcFvqefxUGp$4f13cbe565c52f635557f2dda48d0a8b9e53f3a3121a32fb7cf9ad63a2a4b55b9d876c5d6ff9ab36ec16548fd3fd0f071211e6e16e3855226bdae45cfc7e4628',1,1,'2025-06-04 20:51:05','temp1@example.com','',0),(2,'lolegario','soladochao',1,1,'2025-06-04 20:52:40','lolegario@comnect.com.br','Luciano Olegario',0),(3,'fsilva','#F@36f324$',1,NULL,'2025-06-05 03:07:49','fsilva@comnect.com.br','Fabio Silva',0),(4,'avaz','123mudar',1,NULL,'2025-07-14 13:36:34','avaz@comnect.com.br','Alexandre Vaz',0),(5,'dneto','PNwZaHVo1UGPK4y',1,NULL,'2025-07-21 13:24:24','dneto@comnect.com.br','Danilo Neto',0),(6,'rragga','LjKbe9TBQKXExJw',NULL,NULL,'2025-07-21 17:50:25','rragga@comnect.com.br','Renato Ragga',0),(7,'gmaciel','Suporte!13',NULL,NULL,'2025-07-21 17:50:57','gmaciel@comnect.com.br','Gustavo Maciel',0),(8,'lkaizer','LCK@qweasdzxc4482',NULL,NULL,'2025-07-21 17:51:15','lkaizer@comnect.com.br','Lucas Kaizer',0),(9,'msilva','Flores@07',NULL,NULL,'2025-07-21 17:51:32','msilva@comnect.com.br','Matheus Silva',0),(10,'halmeida','cXl1zeTlJe8WlhV',NULL,NULL,'2025-07-21 17:51:57','halmeida@comnect.com.br','Henrique Almeida',0),(11,'esilva','P5LwlHKJ6yfWwe3',NULL,NULL,'2025-07-21 17:52:39','esilva@comnect.com.br','Rafael Silva',0),(12,'gmelo','1VgSxGGk1n1tcDL',NULL,NULL,'2025-07-21 17:52:58','gmelo@comnect.com.br','Raysa Melo',0),(13,'suporte','@Telecom01',NULL,NULL,'2025-07-22 19:09:13','suporte@comnect.com.br','Suporte',0),(14,'epinheiro','@Telecom094',NULL,NULL,'2025-07-25 13:49:33','epinheiro@comnect.com.br','Eduardo Pinheiro',1),(15,'crodrigues','iuOdysw1jXbezne',NULL,NULL,'2025-07-25 13:45:42','crodrigues@comnect.com.br','Chrysthyanne Rodrigues',1),(16,'fzanella','ConWsec01!',NULL,NULL,'2025-07-25 13:46:30','fzanella@comnect.com.br','Fernando Zanella',1);
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-11 12:25:36
