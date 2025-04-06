-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : localhost
-- Généré le : dim. 06 avr. 2025 à 02:20
-- Version du serveur : 10.4.28-MariaDB
-- Version de PHP : 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `pmu_ia`
--

-- --------------------------------------------------------

--
-- Structure de la table `chevaux`
--

CREATE TABLE `chevaux` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `age` int(11) DEFAULT NULL,
  `sexe` varchar(10) DEFAULT NULL,
  `proprietaire` varchar(100) DEFAULT NULL,
  `nomPere` varchar(100) DEFAULT NULL,
  `nomMere` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `cote_historique`
--

CREATE TABLE `cote_historique` (
  `id` int(11) NOT NULL,
  `id_participation` int(11) DEFAULT NULL,
  `horodatage` datetime DEFAULT NULL,
  `cote` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `courses`
--

CREATE TABLE `courses` (
  `id` int(11) NOT NULL,
  `date_heure` datetime NOT NULL,
  `lieu` varchar(100) DEFAULT NULL,
  `type_course` varchar(50) DEFAULT NULL,
  `distance` int(11) DEFAULT NULL,
  `terrain` varchar(50) DEFAULT NULL,
  `num_course` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `jockeys`
--

CREATE TABLE `jockeys` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `pays` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `model_versions`
--

CREATE TABLE `model_versions` (
  `id` int(11) NOT NULL,
  `model_type` varchar(50) NOT NULL,
  `hyperparameters` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`hyperparameters`)),
  `training_date` datetime NOT NULL,
  `training_duration` int(11) DEFAULT NULL,
  `accuracy` float DEFAULT NULL,
  `precision_score` float DEFAULT NULL,
  `recall_score` float DEFAULT NULL,
  `f1_score` float DEFAULT NULL,
  `log_loss` float DEFAULT NULL,
  `file_path` varchar(255) NOT NULL,
  `training_data_range` varchar(100) DEFAULT NULL,
  `feature_count` int(11) DEFAULT NULL,
  `sample_count` int(11) DEFAULT NULL,
  `validation_method` varchar(50) DEFAULT NULL,
  `notes` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `participations`
--

CREATE TABLE `participations` (
  `id` int(11) NOT NULL,
  `id_course` int(11) DEFAULT NULL,
  `id_cheval` int(11) DEFAULT NULL,
  `id_jockey` int(11) DEFAULT NULL,
  `position` int(11) DEFAULT NULL,
  `poids` float DEFAULT NULL,
  `est_forfait` tinyint(1) DEFAULT NULL,
  `cote_initiale` float DEFAULT NULL,
  `cote_actuelle` float DEFAULT NULL,
  `statut` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `pmu_cote_evolution`
--

CREATE TABLE `pmu_cote_evolution` (
  `id` int(11) NOT NULL,
  `id_participant` int(11) DEFAULT NULL,
  `horodatage` datetime DEFAULT NULL,
  `cote` float DEFAULT NULL,
  `variation` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `pmu_courses`
--

CREATE TABLE `pmu_courses` (
  `id` int(11) NOT NULL,
  `numReunion` int(11) DEFAULT NULL,
  `numOrdre` int(11) DEFAULT NULL,
  `libelle` varchar(200) DEFAULT NULL,
  `heureDepart` datetime DEFAULT NULL,
  `timezoneOffset` int(11) DEFAULT NULL,
  `distance` int(11) DEFAULT NULL,
  `distanceUnit` varchar(20) DEFAULT NULL,
  `corde` varchar(50) DEFAULT NULL,
  `nombreDeclaresPartants` int(11) DEFAULT NULL,
  `discipline` varchar(50) DEFAULT NULL,
  `specialite` varchar(50) DEFAULT NULL,
  `hippodrome_code` varchar(10) DEFAULT NULL,
  `ordreArrivee` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`ordreArrivee`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `pmu_hippodromes`
--

CREATE TABLE `pmu_hippodromes` (
  `code` varchar(10) NOT NULL,
  `libelleCourt` varchar(100) DEFAULT NULL,
  `libelleLong` varchar(200) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `pmu_participants`
--

CREATE TABLE `pmu_participants` (
  `id` int(11) NOT NULL,
  `id_course` int(11) DEFAULT NULL,
  `numPmu` int(11) DEFAULT NULL,
  `nom` varchar(100) DEFAULT NULL,
  `age` int(11) DEFAULT NULL,
  `sexe` varchar(20) DEFAULT NULL,
  `race` varchar(50) DEFAULT NULL,
  `statut` varchar(50) DEFAULT NULL,
  `driver` varchar(100) DEFAULT NULL,
  `entraineur` varchar(100) DEFAULT NULL,
  `proprietaire` varchar(100) DEFAULT NULL,
  `musique` varchar(255) DEFAULT NULL,
  `incident` varchar(100) DEFAULT NULL,
  `ordreArrivee` int(11) DEFAULT NULL,
  `tempsObtenu` int(11) DEFAULT NULL,
  `reductionKilometrique` int(11) DEFAULT NULL,
  `dernierRapportDirect` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`dernierRapportDirect`)),
  `dernierRapportReference` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`dernierRapportReference`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `pmu_pays`
--

CREATE TABLE `pmu_pays` (
  `code` varchar(3) NOT NULL,
  `libelle` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `pmu_reunions`
--

CREATE TABLE `pmu_reunions` (
  `id` int(11) NOT NULL,
  `cached` int(11) DEFAULT NULL,
  `timezoneOffset` int(11) DEFAULT NULL,
  `dateReunion` datetime DEFAULT NULL,
  `numOfficiel` int(11) DEFAULT NULL,
  `numOfficielReunionPrecedente` int(11) DEFAULT NULL,
  `numOfficielReunionSuivante` int(11) DEFAULT NULL,
  `numExterne` int(11) DEFAULT NULL,
  `nature` varchar(50) DEFAULT NULL,
  `audience` varchar(50) DEFAULT NULL,
  `statut` varchar(50) DEFAULT NULL,
  `disciplinesMere` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`disciplinesMere`)),
  `specialites` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`specialites`)),
  `derniereReunion` varchar(10) DEFAULT NULL,
  `reportPlusFpaMax` int(11) DEFAULT NULL,
  `hippodrome_code` varchar(10) DEFAULT NULL,
  `pays_code` varchar(3) DEFAULT NULL,
  `nebulositeCode` varchar(20) DEFAULT NULL,
  `nebulositeLibelleCourt` varchar(50) DEFAULT NULL,
  `nebulositeLibelleLong` varchar(200) DEFAULT NULL,
  `temperature` int(11) DEFAULT NULL,
  `forceVent` int(11) DEFAULT NULL,
  `directionVent` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `predictions`
--

CREATE TABLE `predictions` (
  `id` int(11) NOT NULL,
  `id_course` int(11) DEFAULT NULL,
  `horodatage` datetime DEFAULT NULL,
  `prediction` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`prediction`)),
  `note_confiance` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `simulations`
--

CREATE TABLE `simulations` (
  `id` int(11) NOT NULL,
  `utilisateur_id` int(11) DEFAULT NULL,
  `date_simulation` datetime DEFAULT NULL,
  `id_course` int(11) DEFAULT NULL,
  `chevaux_selectionnes` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`chevaux_selectionnes`)),
  `resultat_simule` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`resultat_simule`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Structure de la table `utilisateurs`
--

CREATE TABLE `utilisateurs` (
  `id` int(11) NOT NULL,
  `nom_utilisateur` varchar(50) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `mot_de_passe` varchar(255) DEFAULT NULL,
  `abonnement_actif` tinyint(1) DEFAULT NULL,
  `date_expiration` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `chevaux`
--
ALTER TABLE `chevaux`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `cote_historique`
--
ALTER TABLE `cote_historique`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_participation` (`id_participation`);

--
-- Index pour la table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `jockeys`
--
ALTER TABLE `jockeys`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `model_versions`
--
ALTER TABLE `model_versions`
  ADD PRIMARY KEY (`id`);

--
-- Index pour la table `participations`
--
ALTER TABLE `participations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_course` (`id_course`),
  ADD KEY `id_cheval` (`id_cheval`),
  ADD KEY `id_jockey` (`id_jockey`);

--
-- Index pour la table `pmu_cote_evolution`
--
ALTER TABLE `pmu_cote_evolution`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_participant` (`id_participant`);

--
-- Index pour la table `pmu_courses`
--
ALTER TABLE `pmu_courses`
  ADD PRIMARY KEY (`id`),
  ADD KEY `hippodrome_code` (`hippodrome_code`);

--
-- Index pour la table `pmu_hippodromes`
--
ALTER TABLE `pmu_hippodromes`
  ADD PRIMARY KEY (`code`);

--
-- Index pour la table `pmu_participants`
--
ALTER TABLE `pmu_participants`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_course` (`id_course`);

--
-- Index pour la table `pmu_pays`
--
ALTER TABLE `pmu_pays`
  ADD PRIMARY KEY (`code`);

--
-- Index pour la table `pmu_reunions`
--
ALTER TABLE `pmu_reunions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `hippodrome_code` (`hippodrome_code`),
  ADD KEY `pays_code` (`pays_code`);

--
-- Index pour la table `predictions`
--
ALTER TABLE `predictions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_course` (`id_course`);

--
-- Index pour la table `simulations`
--
ALTER TABLE `simulations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `utilisateur_id` (`utilisateur_id`),
  ADD KEY `id_course` (`id_course`);

--
-- Index pour la table `utilisateurs`
--
ALTER TABLE `utilisateurs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `chevaux`
--
ALTER TABLE `chevaux`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `cote_historique`
--
ALTER TABLE `cote_historique`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `courses`
--
ALTER TABLE `courses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `jockeys`
--
ALTER TABLE `jockeys`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `model_versions`
--
ALTER TABLE `model_versions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `participations`
--
ALTER TABLE `participations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `pmu_cote_evolution`
--
ALTER TABLE `pmu_cote_evolution`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `pmu_courses`
--
ALTER TABLE `pmu_courses`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `pmu_participants`
--
ALTER TABLE `pmu_participants`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `pmu_reunions`
--
ALTER TABLE `pmu_reunions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `predictions`
--
ALTER TABLE `predictions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `simulations`
--
ALTER TABLE `simulations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT pour la table `utilisateurs`
--
ALTER TABLE `utilisateurs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `cote_historique`
--
ALTER TABLE `cote_historique`
  ADD CONSTRAINT `cote_historique_ibfk_1` FOREIGN KEY (`id_participation`) REFERENCES `participations` (`id`);

--
-- Contraintes pour la table `participations`
--
ALTER TABLE `participations`
  ADD CONSTRAINT `participations_ibfk_1` FOREIGN KEY (`id_course`) REFERENCES `courses` (`id`),
  ADD CONSTRAINT `participations_ibfk_2` FOREIGN KEY (`id_cheval`) REFERENCES `chevaux` (`id`),
  ADD CONSTRAINT `participations_ibfk_3` FOREIGN KEY (`id_jockey`) REFERENCES `jockeys` (`id`);

--
-- Contraintes pour la table `pmu_cote_evolution`
--
ALTER TABLE `pmu_cote_evolution`
  ADD CONSTRAINT `pmu_cote_evolution_ibfk_1` FOREIGN KEY (`id_participant`) REFERENCES `pmu_participants` (`id`);

--
-- Contraintes pour la table `pmu_courses`
--
ALTER TABLE `pmu_courses`
  ADD CONSTRAINT `pmu_courses_ibfk_1` FOREIGN KEY (`hippodrome_code`) REFERENCES `pmu_hippodromes` (`code`);

--
-- Contraintes pour la table `pmu_participants`
--
ALTER TABLE `pmu_participants`
  ADD CONSTRAINT `pmu_participants_ibfk_1` FOREIGN KEY (`id_course`) REFERENCES `pmu_courses` (`id`);

--
-- Contraintes pour la table `pmu_reunions`
--
ALTER TABLE `pmu_reunions`
  ADD CONSTRAINT `pmu_reunions_ibfk_1` FOREIGN KEY (`hippodrome_code`) REFERENCES `pmu_hippodromes` (`code`),
  ADD CONSTRAINT `pmu_reunions_ibfk_2` FOREIGN KEY (`pays_code`) REFERENCES `pmu_pays` (`code`);

--
-- Contraintes pour la table `predictions`
--
ALTER TABLE `predictions`
  ADD CONSTRAINT `predictions_ibfk_1` FOREIGN KEY (`id_course`) REFERENCES `courses` (`id`);

--
-- Contraintes pour la table `simulations`
--
ALTER TABLE `simulations`
  ADD CONSTRAINT `simulations_ibfk_1` FOREIGN KEY (`utilisateur_id`) REFERENCES `utilisateurs` (`id`),
  ADD CONSTRAINT `simulations_ibfk_2` FOREIGN KEY (`id_course`) REFERENCES `courses` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
