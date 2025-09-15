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
-- Table structure for table `answer_options`
--

DROP TABLE IF EXISTS `answer_options`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `answer_options` (
  `id` int NOT NULL AUTO_INCREMENT,
  `question_id` int NOT NULL,
  `option_text` varchar(500) NOT NULL,
  `is_correct` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `question_id` (`question_id`),
  CONSTRAINT `answer_options_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=141 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `answer_options`
--

LOCK TABLES `answer_options` WRITE;
/*!40000 ALTER TABLE `answer_options` DISABLE KEYS */;
INSERT INTO `answer_options` VALUES (41,17,'Usar apenas letras minúsculas para facilitar a memorização',0),(42,17,'Ser curta, com no máximo 5 caracteres',0),(43,17,'Ter uma mistura de letras, números e símbolos',1),(44,17,'Usar informações pessoais, como seu nome ou data de nascimento',0),(45,18,'Porque isso pode atrasar o processo de login',0),(46,18,'Porque é mais difícil de lembrar se a senha for a mesma',0),(47,18,'Se uma conta for comprometida, todas as outras contas estão em risco',1),(48,18,'Porque senhas repetidas gastam mais dados da internet',0),(49,19,'Anotar em um pedaço de papel',0),(50,19,'Salvar em um arquivo de texto no computador',0),(51,19,'Decorar todas as senhas na sua memória',0),(52,19,'Usar um gerenciador de senhas',1),(73,25,'Um e-mail que oferece um prêmio em dinheiro.',0),(74,25,'Um e-mail com anúncios de venda.',0),(75,25,'Um e-mail falso que tenta enganar você para que revele informações pessoais.',1),(76,25,'Um e-mail que contém apenas imagens e vídeos, sem texto.',0),(77,26,'Clicar no link imediatamente para não perder a chance.',0),(78,26,'Desconfiar e enviar a mensagem para os seus amigos para que eles também vejam.',0),(79,26,'Desconfiar e apagar a mensagem, pois pode ser um golpe.',1),(80,26,'Responder à mensagem questionando o e-mail.',0),(81,27,'Qualquer software usado para navegar na internet.',0),(82,27,'Um tipo de vírus que infecta apenas computadores linux.',0),(83,27,'Um programa de computador comum.',0),(84,27,'Um software criado para causar danos ao seu computador ou roubar informações.',1),(85,28,'Desligar seu computador ao acessar um site inseguro.',0),(86,28,'Conectar-se a redes Wi-Fi públicas apenas caso tenham senha.',0),(87,28,'Instalar um bom antivírus e mantê-lo sempre atualizado.',1),(88,28,'Baixar programas de sites recomendados por terceiros.',0),(89,29,'Usar redes sociais para fazer novos amigos.',0),(90,29,'A arte de manipular pessoas para que elas revelem informações confidenciais.',1),(91,29,'O processo de construir um site com boa navegação.',0),(92,29,'A habilidade de programar redes sociais.',0),(93,30,'E-mails de phishing são sempre mais curtos que e-mails de spam.',0),(94,30,'E-mails de spam são maliciosos, enquanto os de phishing são apenas propagandas indesejadas.',0),(95,30,'O phishing é uma tentativa de roubar informações, enquanto o spam geralmente é propaganda em massa.',1),(96,30,'Spam é ilegal, enquanto phishing é legal.',0),(97,31,'O Spear Phishing é mais difícil de ser detectado porque não tem erros de português.',0),(98,31,'O Spear Phishing é um ataque direcionado e personalizado a um indivíduo ou grupo.',1),(99,31,'O Spear Phishing usa apenas anexos, não links.',0),(100,31,'O Spear Phishing é um ataque que visa apenas empresas.',0),(101,32,'A mensagem ser muito curta.',0),(102,32,'A urgência e a ameaça de bloqueio, que são táticas comuns em golpes.',1),(103,32,'O e-mail não ter anexos.',0),(104,32,'O logotipo do banco estar um pouco diferente.',0),(105,33,'Clicar no link do e-mail para ter certeza de que está no lugar certo.',0),(106,33,'Digitar o endereço do site diretamente na barra de navegação do seu navegador.',1),(107,33,'Pesquisar o nome da empresa no Google e clicar no primeiro resultado.',0),(108,33,'Passar o link para um amigo verificar antes de você.',0),(109,34,'Passar a senha, pois ele disse que é urgente.',0),(110,34,'Ajudar o colega, mas sem passar a senha, sugerindo que ele procure o setor de TI.',1),(111,34,'Pedir para ele escrever a senha em um papel e entregar para você.',0),(112,34,'Deixar o colega usar seu computador para ele mesmo resolver o problema.',0),(113,35,'Enviar muitos e-mails.',0),(114,35,'Criar um sentimento de urgência, medo ou curiosidade para que você não pense e tome uma atitude rápida.',1),(115,35,'Usar programas de computador para quebrar senhas.',0),(116,35,'Fingir ser outra pessoa.',0),(117,36,'Nunca compartilhar informações pessoais online.',0),(118,36,'Instalar um bom antivírus em todos os seus dispositivos.',0),(119,36,'Manter seu sistema operacional e seus aplicativos sempre atualizados.',0),(120,36,'Questionar toda e qualquer solicitação de dados ou ação urgente, e sempre verificar a autenticidade da fonte através de um canal oficial.',1),(121,37,'Aumentar a velocidade da sua conexão.',0),(122,37,'Apenas proteger o seu computador contra vírus.',0),(123,37,'Criptografar seu tráfego de internet, tornando-o ilegível para quem tentar interceptá-lo.',1),(124,37,'Bloquear todos os anúncios em sites que você visita.',0),(125,38,'O site pode ter erros de formatação.',0),(126,38,'A conexão não é criptografada, o que significa que seus dados podem ser facilmente interceptados.',1),(127,38,'O site é mais lento para carregar.',0),(128,38,'O site pode ter vírus.',0),(129,39,'O firewall protege o computador, enquanto o antivírus protege a rede.',0),(130,39,'O firewall é um software, enquanto o antivírus é um hardware.',0),(131,39,'O firewall controla o tráfego de rede, enquanto o antivírus protege o sistema operacional.',1),(132,39,'O firewall serve apenas para controlar a navegação na internet, e o antivírus é um tipo de software.',0),(133,40,'Pessoas não identificadas podem utiliza-las.',0),(134,40,'Elas possuem navegação restrita e bloqueiam sites importantes.',0),(135,40,'A maioria dessas redes é gerenciada por criminosos para roubar informações.',0),(136,40,'O tráfego de dados não é criptografado, permitindo que possa ser interceptado.',1),(137,41,'Ataque de Negação de Serviço (DDoS).',0),(138,41,'Ataque de Força Bruta (Brute Force).',0),(139,41,'Ataque \"Man-in-the-middle\" (Homem no Meio).',1),(140,41,'Ataque de Phishing.',0);
/*!40000 ALTER TABLE `answer_options` ENABLE KEYS */;
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
