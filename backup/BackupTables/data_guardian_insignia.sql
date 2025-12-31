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
-- Table structure for table `guardian_insignia`
--

DROP TABLE IF EXISTS `guardian_insignia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `guardian_insignia` (
  `guardian_id` int NOT NULL,
  `insignia_id` int NOT NULL,
  `data_conquista` datetime DEFAULT NULL,
  PRIMARY KEY (`guardian_id`,`insignia_id`),
  KEY `insignia_id` (`insignia_id`),
  CONSTRAINT `guardian_insignia_ibfk_1` FOREIGN KEY (`guardian_id`) REFERENCES `guardians` (`id`),
  CONSTRAINT `guardian_insignia_ibfk_2` FOREIGN KEY (`insignia_id`) REFERENCES `insignias` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `guardian_insignia`
--

LOCK TABLES `guardian_insignia` WRITE;
/*!40000 ALTER TABLE `guardian_insignia` DISABLE KEYS */;
INSERT INTO `guardian_insignia` VALUES (1,5,'2025-09-09 20:01:19'),(2,5,'2025-09-10 18:22:09'),(4,5,'2025-09-09 19:59:51'),(5,5,'2025-09-09 20:16:43'),(6,5,'2025-09-09 19:59:57'),(7,5,'2025-09-09 20:19:02'),(8,5,'2025-09-10 16:13:40'),(9,5,'2025-09-10 16:14:59'),(10,5,'2025-09-10 18:21:25'),(11,5,'2025-09-09 18:57:11'),(14,5,'2025-09-10 16:13:49');
/*!40000 ALTER TABLE `guardian_insignia` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-11 12:25:33
