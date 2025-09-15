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
-- Table structure for table `questions`
--

DROP TABLE IF EXISTS `questions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `questions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quiz_id` int DEFAULT NULL,
  `question_text` text NOT NULL,
  `points` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `quiz_id` (`quiz_id`),
  CONSTRAINT `questions_ibfk_1` FOREIGN KEY (`quiz_id`) REFERENCES `quizzes` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `questions`
--

LOCK TABLES `questions` WRITE;
/*!40000 ALTER TABLE `questions` DISABLE KEYS */;
INSERT INTO `questions` VALUES (17,15,'Qual é a característica mais importante de uma senha forte?',3),(18,15,'Por que não é seguro usar a mesma senha em várias contas diferentes?',3),(19,15,'Qual das seguintes opções é a forma mais segura de armazenar e gerenciar todas as suas senhas?',3),(25,17,'O que é um e-mail de \"phishing\"?',3),(26,17,'Se você receber uma mensagem em seu e-mail pessoal dizendo que ganhou um prêmio, mas precisa clicar em um link para \"resgatá-lo\", o que você deve fazer?',3),(27,17,'O que é \"malware\"?',3),(28,17,'Qual é a melhor forma de se proteger contra um vírus de computador?',3),(29,17,'O que significa \"engenharia social\" no contexto de golpes online?',3),(30,18,'O que é a principal diferença entre um e-mail de phishing e um e-mail de spam?',3),(31,18,'Qual é a principal característica que diferencia o \"Spear Phishing\" do \"Phishing\" comum?',3),(32,18,'Um e-mail da sua empresa de banco avisa que sua conta será bloqueada se você não clicar em um link e verificar suas informações imediatamente. Qual é a principal suspeita nesse e-mail?',3),(33,18,'Qual é a maneira mais segura de acessar um site importante (como seu e-mail de trabalho ou banco online) após receber um e-mail com um link?',3),(34,18,'Um colega de trabalho que você não conhece muito bem te pede sua senha de acesso a um sistema, alegando que \"precisa muito\" para resolver um problema urgente. O que você deve fazer?',3),(35,18,'Qual é a principal tática que um golpista usa para convencer uma pessoa a dar informações confidenciais?',3),(36,18,'Qual é a melhor forma de se proteger contra a maioria dos golpes que usam engenharia social (seja por e-mail, telefone ou mensagem)?',3),(37,18,'Qual é a principal função de uma VPN (Rede Privada Virtual) ao navegar na internet em uma rede Wi-Fi pública?',3),(38,18,'Você acessou um site e percebeu que a URL começa com \"http://\" em vez de \"https://\". Qual é o risco principal de continuar navegando nesse site, especialmente se ele pedir informações pessoais?',3),(39,19,'Qual é a principal diferença entre um firewall de rede e um antivírus?',3),(40,19,'Por que as redes Wi-Fi públicas e abertas (sem senha) são consideradas um risco de segurança?',3),(41,19,'Qual dos seguintes ataques de rede envolve o criminoso \"escutando\" a comunicação entre dois computadores para roubar dados, sem que as vítimas percebam?',3);
/*!40000 ALTER TABLE `questions` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-11 12:25:35
