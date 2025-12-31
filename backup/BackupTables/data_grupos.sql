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
-- Table structure for table `grupos`
--

DROP TABLE IF EXISTS `grupos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `grupos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `chave` varchar(10) NOT NULL,
  `nome` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `opcoes` text,
  `bloqueado` varchar(20) DEFAULT NULL,
  `qtd_operadores` int DEFAULT NULL,
  `smtp_ativo` varchar(10) DEFAULT NULL,
  `criado_em` datetime DEFAULT NULL,
  `atualizado_em` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `chave` (`chave`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `grupos`
--

LOCK TABLES `grupos` WRITE;
/*!40000 ALTER TABLE `grupos` DISABLE KEYS */;
INSERT INTO `grupos` VALUES (1,'000005','CSM','csm@dominio.com.br','<span class=\"fa fa-globe text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Automaticamente\"></span>  <span class=\"fa fa-eye text-info fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (Online) Automaticamente\"></span>  <span class=\"fa fa-pencil text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores nas Transferências\"></span>  <span class=\"fa fa-user text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (por Cliente e Especialidade)\"></span>  <span class=\"fa fa-random text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Aleatoriamente\"></span>  ','',1,'N','2025-08-07 11:26:08','2025-08-07 11:26:08'),(2,'000003','DEV','dev@dominio.com.br','<span class=\"fa fa-globe text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Automaticamente\"></span>  <span class=\"fa fa-eye text-info fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (Online) Automaticamente\"></span>  <span class=\"fa fa-pencil text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores nas Transferências\"></span>  <span class=\"fa fa-user text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (por Cliente e Especialidade)\"></span>  <span class=\"fa fa-random text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Aleatoriamente\"></span>  ','',4,'N','2025-08-07 11:26:08','2025-08-07 11:26:08'),(3,'000010','FIELD','field@dominio.com.br','<span class=\"fa fa-globe text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Automaticamente\"></span>  <span class=\"fa fa-eye text-info fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (Online) Automaticamente\"></span>  <span class=\"fa fa-pencil text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores nas Transferências\"></span>  <span class=\"fa fa-user text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (por Cliente e Especialidade)\"></span>  <span class=\"fa fa-random text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Aleatoriamente\"></span>  ','N',0,'N','2025-08-07 11:26:08','2025-08-07 11:26:08'),(4,'000004','INFOSEC','infosec@dominio.com.br','<span class=\"fa fa-globe text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Automaticamente\"></span>  <span class=\"fa fa-eye text-info fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (Online) Automaticamente\"></span>  <span class=\"fa fa-pencil text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores nas Transferências\"></span>  <span class=\"fa fa-user text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (por Cliente e Especialidade)\"></span>  <span class=\"fa fa-random text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Aleatoriamente\"></span>  ','',2,'N','2025-08-07 11:26:08','2025-08-07 11:26:08'),(5,'000002','NOC','noc@dominio.com.br','<span class=\"fa fa-globe text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Automaticamente\"></span>  <span class=\"fa fa-eye text-info fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (Online) Automaticamente\"></span>  <span class=\"fa fa-pencil text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores nas Transferências\"></span>  <span class=\"fa fa-user text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (por Cliente e Especialidade)\"></span>  <span class=\"fa fa-random text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Aleatoriamente\"></span>  ','',1,'N','2025-08-07 11:26:08','2025-08-07 11:26:08'),(6,'000001','SUPORTE COMNEcT','atendimento.suporte@comnect.com.br','<span class=\"fa fa-globe text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Automaticamente\"></span>  <span class=\"fa fa-eye text-info fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (Online) Automaticamente\"></span>  <span class=\"fa fa-pencil text-warning fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores nas Transferências\"></span>  <span class=\"fa fa-user text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (por Cliente e Especialidade)\"></span>  <span class=\"fa fa-random text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Aleatoriamente\"></span>  ','S',10,'N','2025-08-07 11:26:08','2025-08-07 11:26:08'),(7,'000009','SUPORTE TI','suporteti@dominio.com.br','<span class=\"fa fa-globe text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Automaticamente\"></span>  <span class=\"fa fa-eye text-info fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (Online) Automaticamente\"></span>  <span class=\"fa fa-pencil text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores nas Transferências\"></span>  <span class=\"fa fa-user text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (por Cliente e Especialidade)\"></span>  <span class=\"fa fa-random text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Aleatoriamente\"></span>  ','N',0,'N','2025-08-07 11:26:08','2025-08-07 11:26:08'),(8,'000012','SUPORTE VYRTOS','atendimento.suporte@vyrtos.com.br','<span class=\"fa fa-globe text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Automaticamente\"></span>  <span class=\"fa fa-eye text-info fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (Online) Automaticamente\"></span>  <span class=\"fa fa-pencil text-warning fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores nas Transferências\"></span>  <span class=\"fa fa-user text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores (por Cliente e Especialidade)\"></span>  <span class=\"fa fa-random text-muted fa-fw\" data-toggle=\"tooltip\" data-placement=\"auto top\" title=\"Distribuir Chamados para os Operadores Aleatoriamente\"></span>  ','N',0,'N','2025-08-07 11:26:08','2025-08-07 11:26:08');
/*!40000 ALTER TABLE `grupos` ENABLE KEYS */;
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
