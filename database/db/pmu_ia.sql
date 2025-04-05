-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Hôte : localhost
-- Généré le : dim. 06 avr. 2025 à 01:05
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
  `proprietaire` varchar(100) DEFAULT NULL
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
  `model_type` varchar(50) NOT NULL COMMENT 'Type de modèle (xgboost, random_forest, etc.)',
  `hyperparameters` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT 'Paramètres du modèle au format JSON' CHECK (json_valid(`hyperparameters`)),
  `training_date` datetime NOT NULL COMMENT 'Date d''entraînement du modèle',
  `training_duration` int(11) DEFAULT NULL COMMENT 'Durée d''entraînement en secondes',
  `accuracy` float DEFAULT NULL COMMENT 'Précision globale du modèle',
  `precision_score` float DEFAULT NULL COMMENT 'Score de précision',
  `recall_score` float DEFAULT NULL COMMENT 'Score de rappel',
  `f1_score` float DEFAULT NULL COMMENT 'Score F1',
  `log_loss` float DEFAULT NULL COMMENT 'Log loss',
  `file_path` varchar(255) NOT NULL COMMENT 'Chemin du fichier du modèle enregistré',
  `training_data_range` varchar(100) DEFAULT NULL COMMENT 'Période des données d''entraînement',
  `feature_count` int(11) DEFAULT NULL COMMENT 'Nombre de caractéristiques utilisées',
  `sample_count` int(11) DEFAULT NULL COMMENT 'Nombre d''échantillons d''entraînement',
  `validation_method` varchar(50) DEFAULT NULL COMMENT 'Méthode de validation (cross-validation, hold-out, etc.)',
  `notes` text DEFAULT NULL COMMENT 'Notes additionnelles sur le modèle',
  `is_active` tinyint(1) DEFAULT 0 COMMENT 'Indique si c''est le modèle actif actuellement',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Versions des modèles de prédiction avec leurs performances';

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
  `est_forfait` tinyint(1) DEFAULT 0,
  `cote_initiale` float DEFAULT NULL,
  `cote_actuelle` float DEFAULT NULL,
  `statut` varchar(50) DEFAULT NULL
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
  `abonnement_actif` tinyint(1) DEFAULT 0,
  `date_expiration` date DEFAULT NULL
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
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_model_type` (`model_type`),
  ADD KEY `idx_training_date` (`training_date`),
  ADD KEY `idx_is_active` (`is_active`);

--
-- Index pour la table `participations`
--
ALTER TABLE `participations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_course` (`id_course`),
  ADD KEY `id_cheval` (`id_cheval`),
  ADD KEY `id_jockey` (`id_jockey`);

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
