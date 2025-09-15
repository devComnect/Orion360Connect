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
-- Table structure for table `insignias`
--

DROP TABLE IF EXISTS `insignias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `insignias` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) NOT NULL,
  `descricao` text NOT NULL,
  `requisito_score` int DEFAULT NULL,
  `caminho_imagem` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nome` (`nome`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `insignias`
--

LOCK TABLES `insignias` WRITE;
/*!40000 ALTER TABLE `insignias` DISABLE KEYS */;
INSERT INTO `insignias` VALUES (5,'Batismo de Fogo','Responda ao seu primeiro quiz.	',0,'img/conquistas/batismo-de-fogo.png'),(6,'Olhos de Águia','Realize seu primeiro reporte de phishing corretamente (simulado/ real).',0,'img/conquistas/olhos-de-aguia.png'),(7,'Guardião Vigilante','Reporte 5 phishings simulados corretamente.	',0,'img/conquistas/guardiao-vigilante.png'),(8,'Caça-Fantasmas','Reportou um e-mail de phishing real.',0,'img/conquistas/caca-fantasma.png'),(9,'Maratonista','Tire a pontuação máxima em 7 quizzes durante 1 semana.',0,'img/conquistas/maratonista.png'),(10,'CDF da Segurança','Tire a pontuação máxima em quizzes durante um mês.',0,'img/conquistas/cdf.png'),(11,'Muralha da China','Passe 10 campanhas consecutivas sem clicar em nenhum link de phishing simulado.\r\n',0,'img/conquistas/muralha.png'),(12,'Bom Samaritano','Ajudou a equipe de segurança com sugestões implementadas.',0,'img/conquistas/bom-samaritano.png'),(13,'Recruta Estelar','Alcançe o Nível 2 na plataforma.',0,'img/conquistas/estelar.png'),(14,'Veterano','Acumulou 1000 pontos',1000,'img/conquistas/veterano.png'),(15,'Resposta Rápida	','Reporte um phishing simulado nos primeiros 10 minutos após o envio.',0,'img/conquistas/resposta-rapida.png'),(16,'Defensor de Elite','Reporte um total de 10 phishings simulados.	',0,'img/conquistas/defensor-elite.png'),(17,'Expert em Ransomware','Obtenha pontuação máxima em um quiz da categoria \"Hardcore\".',0,'img/conquistas/expert-ransomware.png'),(18,'O Número Um','Termine um semestre 1º lugar do ranking individual.',0,'img/conquistas/o-numero-um.png'),(19,'Sempre Presente','Reponda todos os quizzes durante 30 dias.',0,'img/conquistas/sempre-presente.png'),(20,'Sentinela Físico','Reporte uma vulnerabilidade de segurança física válida.',0,'img/conquistas/sentinela-fisico.png'),(21,'Departamento Destaque	','Faça parte do departamento que terminou o semestre em 1º lugar no ranking.	',0,'img/conquistas/departamento-destaque.png'),(22,'Fortaleza Digital','Passe 5 campanhas consecutivas sem clicar em nenhum link de phishing simulado.	',0,'img/conquistas/fortaleza-digital.png'),(23,'Desbravador','Seja o primeiro a reportar um e-mail de phishing simulado.',0,'img/conquistas/desbravador.png'),(24,'Mente Brilhante','Complete um total de 50 quizzes.	',0,'img/conquistas/mente-brilhante.png');
/*!40000 ALTER TABLE `insignias` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-11 12:25:38
