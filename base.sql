PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

DROP TABLE IF EXISTS versions;
CREATE TABLE versions (
	id INTEGER NOT NULL, 
	version_group_id INTEGER NOT NULL, 
	name VARCHAR(32) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(version_group_id) REFERENCES version_groups (id)
);
INSERT INTO "versions" VALUES(1,1,'Red');
INSERT INTO "versions" VALUES(2,1,'Blue');
INSERT INTO "versions" VALUES(3,2,'Yellow');
INSERT INTO "versions" VALUES(4,3,'Gold');
INSERT INTO "versions" VALUES(5,3,'Silver');
INSERT INTO "versions" VALUES(6,4,'Crystal');
INSERT INTO "versions" VALUES(7,5,'Ruby');
INSERT INTO "versions" VALUES(8,5,'Sapphire');
INSERT INTO "versions" VALUES(9,6,'Emerald');
INSERT INTO "versions" VALUES(10,7,'FireRed');
INSERT INTO "versions" VALUES(11,7,'LeafGreen');
INSERT INTO "versions" VALUES(12,8,'Diamond');
INSERT INTO "versions" VALUES(13,8,'Pearl');
INSERT INTO "versions" VALUES(14,9,'Platinum');
INSERT INTO "versions" VALUES(15,10,'HeartGold');
INSERT INTO "versions" VALUES(16,10,'SoulSilver');
INSERT INTO "versions" VALUES(17,11,'Black');
INSERT INTO "versions" VALUES(18,11,'White');

DROP TABLE IF EXISTS version_groups;
CREATE TABLE version_groups (
	id INTEGER NOT NULL, 
	generation_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(generation_id) REFERENCES generations (id)
);
INSERT INTO "version_groups" VALUES(1,1);
INSERT INTO "version_groups" VALUES(2,1);
INSERT INTO "version_groups" VALUES(3,2);
INSERT INTO "version_groups" VALUES(4,2);
INSERT INTO "version_groups" VALUES(5,3);
INSERT INTO "version_groups" VALUES(6,3);
INSERT INTO "version_groups" VALUES(7,3);
INSERT INTO "version_groups" VALUES(8,4);
INSERT INTO "version_groups" VALUES(9,4);
INSERT INTO "version_groups" VALUES(10,4);
INSERT INTO "version_groups" VALUES(11,5);

DROP TABLE IF EXISTS regions;
CREATE TABLE regions (
	id INTEGER NOT NULL, 
	name VARCHAR(16) NOT NULL, 
	PRIMARY KEY (id)
);
INSERT INTO "regions" VALUES(1,'Kanto');
INSERT INTO "regions" VALUES(2,'Johto');
INSERT INTO "regions" VALUES(3,'Hoenn');
INSERT INTO "regions" VALUES(4,'Sinnoh');
INSERT INTO "regions" VALUES(5,'Isshu');

DROP TABLE IF EXISTS generations;
CREATE TABLE generations (
	id INTEGER NOT NULL, 
	main_region_id INTEGER, 
	canonical_pokedex_id INTEGER, 
	name VARCHAR(16) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(main_region_id) REFERENCES regions (id), 
	FOREIGN KEY(canonical_pokedex_id) REFERENCES pokedexes (id)
);
INSERT INTO "generations" VALUES(1,1,2,'Generation I');
INSERT INTO "generations" VALUES(2,2,7,'Generation II');
INSERT INTO "generations" VALUES(3,3,4,'Generation III');
INSERT INTO "generations" VALUES(4,4,6,'Generation IV');
INSERT INTO "generations" VALUES(5,5,8,'Generation V');


DROP TABLE IF EXISTS locations;
CREATE TABLE locations (
    id INTEGER NOT NULL, 
    region_id INTEGER, 
    name VARCHAR(64) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(region_id) REFERENCES regions (id)
);

DROP TABLE IF EXISTS location_areas;
CREATE TABLE location_areas (
    id INTEGER NOT NULL, 
    location_id INTEGER NOT NULL, 
    internal_id INTEGER, 
    name VARCHAR(64), 
    PRIMARY KEY (id), 
    FOREIGN KEY(location_id) REFERENCES locations (id)
);

DROP TABLE IF EXISTS location_area_encounter_rates;
CREATE TABLE location_area_encounter_rates (
    location_area_id INTEGER NOT NULL, 
    encounter_method_id INTEGER NOT NULL, 
    version_id INTEGER NOT NULL, 
    rate INTEGER, 
    PRIMARY KEY (location_area_id, encounter_method_id, version_id), 
    FOREIGN KEY(location_area_id) REFERENCES location_areas (id), 
    FOREIGN KEY(version_id) REFERENCES versions (id), 
    FOREIGN KEY(encounter_method_id) REFERENCES encounter_methods (id)
);


DROP TABLE IF EXISTS encounter_conditions;
CREATE TABLE encounter_conditions (
	id INTEGER NOT NULL, 
	identifier VARCHAR(64) NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);
INSERT INTO "encounter_conditions" VALUES(1,'swarm','Swarm');
INSERT INTO "encounter_conditions" VALUES(2,'time','Time of day');
INSERT INTO "encounter_conditions" VALUES(3,'radar','PokeRadar');
INSERT INTO "encounter_conditions" VALUES(4,'slot2','Gen 3 game in slot 2');
INSERT INTO "encounter_conditions" VALUES(5,'radio','Radio');
INSERT INTO "encounter_conditions" VALUES(8,'season','Season');
INSERT INTO "encounter_conditions" VALUES(9,'spots','Wiggling Spots');

DROP TABLE IF EXISTS encounter_condition_values;
CREATE TABLE encounter_condition_values (
	id INTEGER NOT NULL, 
	encounter_condition_id INTEGER NOT NULL, 
	identifier VARCHAR(64) NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	is_default BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(encounter_condition_id) REFERENCES encounter_conditions (id), 
	CHECK (is_default IN (0, 1))
);
INSERT INTO "encounter_condition_values" VALUES(1,1,'swarm','During a swarm',0);
INSERT INTO "encounter_condition_values" VALUES(2,1,'','Not during a swarm',1);
INSERT INTO "encounter_condition_values" VALUES(3,2,'morning','In the morning',0);
INSERT INTO "encounter_condition_values" VALUES(4,2,'day','During the day',1);
INSERT INTO "encounter_condition_values" VALUES(5,2,'night','At night',0);
INSERT INTO "encounter_condition_values" VALUES(6,3,'radar','Using PokéRadar',0);
INSERT INTO "encounter_condition_values" VALUES(7,3,'','Not using PokéRadar',1);
INSERT INTO "encounter_condition_values" VALUES(8,4,'','No game in slot 2',1);
INSERT INTO "encounter_condition_values" VALUES(9,4,'ruby','Ruby in slot 2',0);
INSERT INTO "encounter_condition_values" VALUES(10,4,'sapphire','Sapphire in slot 2',0);
INSERT INTO "encounter_condition_values" VALUES(11,4,'emerald','Emerald in slot 2',0);
INSERT INTO "encounter_condition_values" VALUES(12,4,'firered','FireRed in slot 2',0);
INSERT INTO "encounter_condition_values" VALUES(13,4,'leafgreen','LeafGreen in slot 2',0);
INSERT INTO "encounter_condition_values" VALUES(14,5,'','Radio off',1);
INSERT INTO "encounter_condition_values" VALUES(15,5,'hoenn','Hoenn radio',0);
INSERT INTO "encounter_condition_values" VALUES(16,5,'sinnoh','Sinnoh radio',0);
INSERT INTO "encounter_condition_values" VALUES(21,8,'spring','During Spring',0);
INSERT INTO "encounter_condition_values" VALUES(22,8,'summer','During Summer',0);
INSERT INTO "encounter_condition_values" VALUES(23,8,'autumn','During Autumn',0);
INSERT INTO "encounter_condition_values" VALUES(24,8,'winter','During Winter',0);
INSERT INTO "encounter_condition_values" VALUES(25,9,'','No Spots',1);
INSERT INTO "encounter_condition_values" VALUES(26,9,'spots','In a wiggling spot',0);

DROP TABLE IF EXISTS encounter_slots;
CREATE TABLE encounter_slots (
	id INTEGER NOT NULL, 
	version_group_id INTEGER NOT NULL, 
	encounter_method_id INTEGER NOT NULL, 
	encounter_terrain_id INTEGER, 
	slot INTEGER, 
	rarity INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(version_group_id) REFERENCES version_groups (id), 
	FOREIGN KEY(encounter_method_id) REFERENCES encounter_methods (id)
	FOREIGN KEY(encounter_terrain_id) REFERENCES encounter_terrains (id)
);

DROP TABLE IF EXISTS encounters;
CREATE TABLE encounters (
	id INTEGER NOT NULL, 
	version_id INTEGER NOT NULL, 
	location_area_id INTEGER NOT NULL, 
	encounter_slot_id INTEGER NOT NULL, 
	pokemon_id INTEGER NOT NULL, 
	min_level INTEGER NOT NULL, 
	max_level INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(version_id) REFERENCES versions (id), 
	FOREIGN KEY(location_area_id) REFERENCES location_areas (id), 
	FOREIGN KEY(encounter_slot_id) REFERENCES encounter_slots (id), 
	FOREIGN KEY(pokemon_id) REFERENCES pokemon (id)
);

DROP TABLE IF EXISTS encounter_condition_value_map;
CREATE TABLE encounter_condition_value_map (
	encounter_id INTEGER NOT NULL, 
	encounter_condition_value_id INTEGER NOT NULL, 
	PRIMARY KEY (encounter_id, encounter_condition_value_id), 
	FOREIGN KEY(encounter_id) REFERENCES encounters (id), 
	FOREIGN KEY(encounter_condition_value_id) REFERENCES encounter_condition_values (id)
);

DROP TABLE IF EXISTS encounter_methods;
CREATE TABLE encounter_methods (
	id INTEGER NOT NULL, 
	identifier STRING NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	PRIMARY KEY (id)
);
INSERT INTO "encounter_methods" VALUES(1,'walk','Walking');
INSERT INTO "encounter_methods" VALUES(2,'old-rod','Fishing with an Old Rod');
INSERT INTO "encounter_methods" VALUES(3,'good-rod','Fishing with a Good Rod');
INSERT INTO "encounter_methods" VALUES(4,'super-rod','Fishing with a Super Rod');
INSERT INTO "encounter_methods" VALUES(5,'surf','Surfing');
INSERT INTO "encounter_methods" VALUES(6,'rock-smash','Smashing rocks');
INSERT INTO "encounter_methods" VALUES(7,'headbutt','Headbutting trees');
INSERT INTO "encounter_methods" VALUES(8,'fish','Fishing in BW');

DROP TABLE IF EXISTS encounter_terrains;
CREATE TABLE encounter_terrains (
	id INTEGER NOT NULL,
	identifier STRING NOT NULL,
	PRIMARY KEY (id)
);
INSERT INTO "encounter_terrains" VALUES(1,'grass');
INSERT INTO "encounter_terrains" VALUES(2,'dark-grass');
INSERT INTO "encounter_terrains" VALUES(3,'cave');
INSERT INTO "encounter_terrains" VALUES(4,'bridge');

DROP TABLE IF EXISTS pokemon;
CREATE TABLE pokemon (
	id INTEGER NOT NULL,
	name STRING,
	PRIMARY KEY (id)
);

INSERT INTO "pokemon" VALUES(1,'Bulbasaur');
INSERT INTO "pokemon" VALUES(2,'Ivysaur');
INSERT INTO "pokemon" VALUES(3,'Venusaur');
INSERT INTO "pokemon" VALUES(4,'Charmander');
INSERT INTO "pokemon" VALUES(5,'Charmeleon');
INSERT INTO "pokemon" VALUES(6,'Charizard');
INSERT INTO "pokemon" VALUES(7,'Squirtle');
INSERT INTO "pokemon" VALUES(8,'Wartortle');
INSERT INTO "pokemon" VALUES(9,'Blastoise');
INSERT INTO "pokemon" VALUES(10,'Caterpie');
INSERT INTO "pokemon" VALUES(11,'Metapod');
INSERT INTO "pokemon" VALUES(12,'Butterfree');
INSERT INTO "pokemon" VALUES(13,'Weedle');
INSERT INTO "pokemon" VALUES(14,'Kakuna');
INSERT INTO "pokemon" VALUES(15,'Beedrill');
INSERT INTO "pokemon" VALUES(16,'Pidgey');
INSERT INTO "pokemon" VALUES(17,'Pidgeotto');
INSERT INTO "pokemon" VALUES(18,'Pidgeot');
INSERT INTO "pokemon" VALUES(19,'Rattata');
INSERT INTO "pokemon" VALUES(20,'Raticate');
INSERT INTO "pokemon" VALUES(21,'Spearow');
INSERT INTO "pokemon" VALUES(22,'Fearow');
INSERT INTO "pokemon" VALUES(23,'Ekans');
INSERT INTO "pokemon" VALUES(24,'Arbok');
INSERT INTO "pokemon" VALUES(25,'Pikachu');
INSERT INTO "pokemon" VALUES(26,'Raichu');
INSERT INTO "pokemon" VALUES(27,'Sandshrew');
INSERT INTO "pokemon" VALUES(28,'Sandslash');
INSERT INTO "pokemon" VALUES(29,'Nidoran♀');
INSERT INTO "pokemon" VALUES(30,'Nidorina');
INSERT INTO "pokemon" VALUES(31,'Nidoqueen');
INSERT INTO "pokemon" VALUES(32,'Nidoran♂');
INSERT INTO "pokemon" VALUES(33,'Nidorino');
INSERT INTO "pokemon" VALUES(34,'Nidoking');
INSERT INTO "pokemon" VALUES(35,'Clefairy');
INSERT INTO "pokemon" VALUES(36,'Clefable');
INSERT INTO "pokemon" VALUES(37,'Vulpix');
INSERT INTO "pokemon" VALUES(38,'Ninetales');
INSERT INTO "pokemon" VALUES(39,'Jigglypuff');
INSERT INTO "pokemon" VALUES(40,'Wigglytuff');
INSERT INTO "pokemon" VALUES(41,'Zubat');
INSERT INTO "pokemon" VALUES(42,'Golbat');
INSERT INTO "pokemon" VALUES(43,'Oddish');
INSERT INTO "pokemon" VALUES(44,'Gloom');
INSERT INTO "pokemon" VALUES(45,'Vileplume');
INSERT INTO "pokemon" VALUES(46,'Paras');
INSERT INTO "pokemon" VALUES(47,'Parasect');
INSERT INTO "pokemon" VALUES(48,'Venonat');
INSERT INTO "pokemon" VALUES(49,'Venomoth');
INSERT INTO "pokemon" VALUES(50,'Diglett');
INSERT INTO "pokemon" VALUES(51,'Dugtrio');
INSERT INTO "pokemon" VALUES(52,'Meowth');
INSERT INTO "pokemon" VALUES(53,'Persian');
INSERT INTO "pokemon" VALUES(54,'Psyduck');
INSERT INTO "pokemon" VALUES(55,'Golduck');
INSERT INTO "pokemon" VALUES(56,'Mankey');
INSERT INTO "pokemon" VALUES(57,'Primeape');
INSERT INTO "pokemon" VALUES(58,'Growlithe');
INSERT INTO "pokemon" VALUES(59,'Arcanine');
INSERT INTO "pokemon" VALUES(60,'Poliwag');
INSERT INTO "pokemon" VALUES(61,'Poliwhirl');
INSERT INTO "pokemon" VALUES(62,'Poliwrath');
INSERT INTO "pokemon" VALUES(63,'Abra');
INSERT INTO "pokemon" VALUES(64,'Kadabra');
INSERT INTO "pokemon" VALUES(65,'Alakazam');
INSERT INTO "pokemon" VALUES(66,'Machop');
INSERT INTO "pokemon" VALUES(67,'Machoke');
INSERT INTO "pokemon" VALUES(68,'Machamp');
INSERT INTO "pokemon" VALUES(69,'Bellsprout');
INSERT INTO "pokemon" VALUES(70,'Weepinbell');
INSERT INTO "pokemon" VALUES(71,'Victreebel');
INSERT INTO "pokemon" VALUES(72,'Tentacool');
INSERT INTO "pokemon" VALUES(73,'Tentacruel');
INSERT INTO "pokemon" VALUES(74,'Geodude');
INSERT INTO "pokemon" VALUES(75,'Graveler');
INSERT INTO "pokemon" VALUES(76,'Golem');
INSERT INTO "pokemon" VALUES(77,'Ponyta');
INSERT INTO "pokemon" VALUES(78,'Rapidash');
INSERT INTO "pokemon" VALUES(79,'Slowpoke');
INSERT INTO "pokemon" VALUES(80,'Slowbro');
INSERT INTO "pokemon" VALUES(81,'Magnemite');
INSERT INTO "pokemon" VALUES(82,'Magneton');
INSERT INTO "pokemon" VALUES(83,'Farfetch''d');
INSERT INTO "pokemon" VALUES(84,'Doduo');
INSERT INTO "pokemon" VALUES(85,'Dodrio');
INSERT INTO "pokemon" VALUES(86,'Seel');
INSERT INTO "pokemon" VALUES(87,'Dewgong');
INSERT INTO "pokemon" VALUES(88,'Grimer');
INSERT INTO "pokemon" VALUES(89,'Muk');
INSERT INTO "pokemon" VALUES(90,'Shellder');
INSERT INTO "pokemon" VALUES(91,'Cloyster');
INSERT INTO "pokemon" VALUES(92,'Gastly');
INSERT INTO "pokemon" VALUES(93,'Haunter');
INSERT INTO "pokemon" VALUES(94,'Gengar');
INSERT INTO "pokemon" VALUES(95,'Onix');
INSERT INTO "pokemon" VALUES(96,'Drowzee');
INSERT INTO "pokemon" VALUES(97,'Hypno');
INSERT INTO "pokemon" VALUES(98,'Krabby');
INSERT INTO "pokemon" VALUES(99,'Kingler');
INSERT INTO "pokemon" VALUES(100,'Voltorb');
INSERT INTO "pokemon" VALUES(101,'Electrode');
INSERT INTO "pokemon" VALUES(102,'Exeggcute');
INSERT INTO "pokemon" VALUES(103,'Exeggutor');
INSERT INTO "pokemon" VALUES(104,'Cubone');
INSERT INTO "pokemon" VALUES(105,'Marowak');
INSERT INTO "pokemon" VALUES(106,'Hitmonlee');
INSERT INTO "pokemon" VALUES(107,'Hitmonchan');
INSERT INTO "pokemon" VALUES(108,'Lickitung');
INSERT INTO "pokemon" VALUES(109,'Koffing');
INSERT INTO "pokemon" VALUES(110,'Weezing');
INSERT INTO "pokemon" VALUES(111,'Rhyhorn');
INSERT INTO "pokemon" VALUES(112,'Rhydon');
INSERT INTO "pokemon" VALUES(113,'Chansey');
INSERT INTO "pokemon" VALUES(114,'Tangela');
INSERT INTO "pokemon" VALUES(115,'Kangaskhan');
INSERT INTO "pokemon" VALUES(116,'Horsea');
INSERT INTO "pokemon" VALUES(117,'Seadra');
INSERT INTO "pokemon" VALUES(118,'Goldeen');
INSERT INTO "pokemon" VALUES(119,'Seaking');
INSERT INTO "pokemon" VALUES(120,'Staryu');
INSERT INTO "pokemon" VALUES(121,'Starmie');
INSERT INTO "pokemon" VALUES(122,'Mr. Mime');
INSERT INTO "pokemon" VALUES(123,'Scyther');
INSERT INTO "pokemon" VALUES(124,'Jynx');
INSERT INTO "pokemon" VALUES(125,'Electabuzz');
INSERT INTO "pokemon" VALUES(126,'Magmar');
INSERT INTO "pokemon" VALUES(127,'Pinsir');
INSERT INTO "pokemon" VALUES(128,'Tauros');
INSERT INTO "pokemon" VALUES(129,'Magikarp');
INSERT INTO "pokemon" VALUES(130,'Gyarados');
INSERT INTO "pokemon" VALUES(131,'Lapras');
INSERT INTO "pokemon" VALUES(132,'Ditto');
INSERT INTO "pokemon" VALUES(133,'Eevee');
INSERT INTO "pokemon" VALUES(134,'Vaporeon');
INSERT INTO "pokemon" VALUES(135,'Jolteon');
INSERT INTO "pokemon" VALUES(136,'Flareon');
INSERT INTO "pokemon" VALUES(137,'Porygon');
INSERT INTO "pokemon" VALUES(138,'Omanyte');
INSERT INTO "pokemon" VALUES(139,'Omastar');
INSERT INTO "pokemon" VALUES(140,'Kabuto');
INSERT INTO "pokemon" VALUES(141,'Kabutops');
INSERT INTO "pokemon" VALUES(142,'Aerodactyl');
INSERT INTO "pokemon" VALUES(143,'Snorlax');
INSERT INTO "pokemon" VALUES(144,'Articuno');
INSERT INTO "pokemon" VALUES(145,'Zapdos');
INSERT INTO "pokemon" VALUES(146,'Moltres');
INSERT INTO "pokemon" VALUES(147,'Dratini');
INSERT INTO "pokemon" VALUES(148,'Dragonair');
INSERT INTO "pokemon" VALUES(149,'Dragonite');
INSERT INTO "pokemon" VALUES(150,'Mewtwo');
INSERT INTO "pokemon" VALUES(151,'Mew');
INSERT INTO "pokemon" VALUES(152,'Chikorita');
INSERT INTO "pokemon" VALUES(153,'Bayleef');
INSERT INTO "pokemon" VALUES(154,'Meganium');
INSERT INTO "pokemon" VALUES(155,'Cyndaquil');
INSERT INTO "pokemon" VALUES(156,'Quilava');
INSERT INTO "pokemon" VALUES(157,'Typhlosion');
INSERT INTO "pokemon" VALUES(158,'Totodile');
INSERT INTO "pokemon" VALUES(159,'Croconaw');
INSERT INTO "pokemon" VALUES(160,'Feraligatr');
INSERT INTO "pokemon" VALUES(161,'Sentret');
INSERT INTO "pokemon" VALUES(162,'Furret');
INSERT INTO "pokemon" VALUES(163,'Hoothoot');
INSERT INTO "pokemon" VALUES(164,'Noctowl');
INSERT INTO "pokemon" VALUES(165,'Ledyba');
INSERT INTO "pokemon" VALUES(166,'Ledian');
INSERT INTO "pokemon" VALUES(167,'Spinarak');
INSERT INTO "pokemon" VALUES(168,'Ariados');
INSERT INTO "pokemon" VALUES(169,'Crobat');
INSERT INTO "pokemon" VALUES(170,'Chinchou');
INSERT INTO "pokemon" VALUES(171,'Lanturn');
INSERT INTO "pokemon" VALUES(172,'Pichu');
INSERT INTO "pokemon" VALUES(173,'Cleffa');
INSERT INTO "pokemon" VALUES(174,'Igglybuff');
INSERT INTO "pokemon" VALUES(175,'Togepi');
INSERT INTO "pokemon" VALUES(176,'Togetic');
INSERT INTO "pokemon" VALUES(177,'Natu');
INSERT INTO "pokemon" VALUES(178,'Xatu');
INSERT INTO "pokemon" VALUES(179,'Mareep');
INSERT INTO "pokemon" VALUES(180,'Flaaffy');
INSERT INTO "pokemon" VALUES(181,'Ampharos');
INSERT INTO "pokemon" VALUES(182,'Bellossom');
INSERT INTO "pokemon" VALUES(183,'Marill');
INSERT INTO "pokemon" VALUES(184,'Azumarill');
INSERT INTO "pokemon" VALUES(185,'Sudowoodo');
INSERT INTO "pokemon" VALUES(186,'Politoed');
INSERT INTO "pokemon" VALUES(187,'Hoppip');
INSERT INTO "pokemon" VALUES(188,'Skiploom');
INSERT INTO "pokemon" VALUES(189,'Jumpluff');
INSERT INTO "pokemon" VALUES(190,'Aipom');
INSERT INTO "pokemon" VALUES(191,'Sunkern');
INSERT INTO "pokemon" VALUES(192,'Sunflora');
INSERT INTO "pokemon" VALUES(193,'Yanma');
INSERT INTO "pokemon" VALUES(194,'Wooper');
INSERT INTO "pokemon" VALUES(195,'Quagsire');
INSERT INTO "pokemon" VALUES(196,'Espeon');
INSERT INTO "pokemon" VALUES(197,'Umbreon');
INSERT INTO "pokemon" VALUES(198,'Murkrow');
INSERT INTO "pokemon" VALUES(199,'Slowking');
INSERT INTO "pokemon" VALUES(200,'Misdreavus');
INSERT INTO "pokemon" VALUES(201,'Unown');
INSERT INTO "pokemon" VALUES(202,'Wobbuffet');
INSERT INTO "pokemon" VALUES(203,'Girafarig');
INSERT INTO "pokemon" VALUES(204,'Pineco');
INSERT INTO "pokemon" VALUES(205,'Forretress');
INSERT INTO "pokemon" VALUES(206,'Dunsparce');
INSERT INTO "pokemon" VALUES(207,'Gligar');
INSERT INTO "pokemon" VALUES(208,'Steelix');
INSERT INTO "pokemon" VALUES(209,'Snubbull');
INSERT INTO "pokemon" VALUES(210,'Granbull');
INSERT INTO "pokemon" VALUES(211,'Qwilfish');
INSERT INTO "pokemon" VALUES(212,'Scizor');
INSERT INTO "pokemon" VALUES(213,'Shuckle');
INSERT INTO "pokemon" VALUES(214,'Heracross');
INSERT INTO "pokemon" VALUES(215,'Sneasel');
INSERT INTO "pokemon" VALUES(216,'Teddiursa');
INSERT INTO "pokemon" VALUES(217,'Ursaring');
INSERT INTO "pokemon" VALUES(218,'Slugma');
INSERT INTO "pokemon" VALUES(219,'Magcargo');
INSERT INTO "pokemon" VALUES(220,'Swinub');
INSERT INTO "pokemon" VALUES(221,'Piloswine');
INSERT INTO "pokemon" VALUES(222,'Corsola');
INSERT INTO "pokemon" VALUES(223,'Remoraid');
INSERT INTO "pokemon" VALUES(224,'Octillery');
INSERT INTO "pokemon" VALUES(225,'Delibird');
INSERT INTO "pokemon" VALUES(226,'Mantine');
INSERT INTO "pokemon" VALUES(227,'Skarmory');
INSERT INTO "pokemon" VALUES(228,'Houndour');
INSERT INTO "pokemon" VALUES(229,'Houndoom');
INSERT INTO "pokemon" VALUES(230,'Kingdra');
INSERT INTO "pokemon" VALUES(231,'Phanpy');
INSERT INTO "pokemon" VALUES(232,'Donphan');
INSERT INTO "pokemon" VALUES(233,'Porygon2');
INSERT INTO "pokemon" VALUES(234,'Stantler');
INSERT INTO "pokemon" VALUES(235,'Smeargle');
INSERT INTO "pokemon" VALUES(236,'Tyrogue');
INSERT INTO "pokemon" VALUES(237,'Hitmontop');
INSERT INTO "pokemon" VALUES(238,'Smoochum');
INSERT INTO "pokemon" VALUES(239,'Elekid');
INSERT INTO "pokemon" VALUES(240,'Magby');
INSERT INTO "pokemon" VALUES(241,'Miltank');
INSERT INTO "pokemon" VALUES(242,'Blissey');
INSERT INTO "pokemon" VALUES(243,'Raikou');
INSERT INTO "pokemon" VALUES(244,'Entei');
INSERT INTO "pokemon" VALUES(245,'Suicune');
INSERT INTO "pokemon" VALUES(246,'Larvitar');
INSERT INTO "pokemon" VALUES(247,'Pupitar');
INSERT INTO "pokemon" VALUES(248,'Tyranitar');
INSERT INTO "pokemon" VALUES(249,'Lugia');
INSERT INTO "pokemon" VALUES(250,'Ho-Oh');
INSERT INTO "pokemon" VALUES(251,'Celebi');
INSERT INTO "pokemon" VALUES(252,'Treecko');
INSERT INTO "pokemon" VALUES(253,'Grovyle');
INSERT INTO "pokemon" VALUES(254,'Sceptile');
INSERT INTO "pokemon" VALUES(255,'Torchic');
INSERT INTO "pokemon" VALUES(256,'Combusken');
INSERT INTO "pokemon" VALUES(257,'Blaziken');
INSERT INTO "pokemon" VALUES(258,'Mudkip');
INSERT INTO "pokemon" VALUES(259,'Marshtomp');
INSERT INTO "pokemon" VALUES(260,'Swampert');
INSERT INTO "pokemon" VALUES(261,'Poochyena');
INSERT INTO "pokemon" VALUES(262,'Mightyena');
INSERT INTO "pokemon" VALUES(263,'Zigzagoon');
INSERT INTO "pokemon" VALUES(264,'Linoone');
INSERT INTO "pokemon" VALUES(265,'Wurmple');
INSERT INTO "pokemon" VALUES(266,'Silcoon');
INSERT INTO "pokemon" VALUES(267,'Beautifly');
INSERT INTO "pokemon" VALUES(268,'Cascoon');
INSERT INTO "pokemon" VALUES(269,'Dustox');
INSERT INTO "pokemon" VALUES(270,'Lotad');
INSERT INTO "pokemon" VALUES(271,'Lombre');
INSERT INTO "pokemon" VALUES(272,'Ludicolo');
INSERT INTO "pokemon" VALUES(273,'Seedot');
INSERT INTO "pokemon" VALUES(274,'Nuzleaf');
INSERT INTO "pokemon" VALUES(275,'Shiftry');
INSERT INTO "pokemon" VALUES(276,'Taillow');
INSERT INTO "pokemon" VALUES(277,'Swellow');
INSERT INTO "pokemon" VALUES(278,'Wingull');
INSERT INTO "pokemon" VALUES(279,'Pelipper');
INSERT INTO "pokemon" VALUES(280,'Ralts');
INSERT INTO "pokemon" VALUES(281,'Kirlia');
INSERT INTO "pokemon" VALUES(282,'Gardevoir');
INSERT INTO "pokemon" VALUES(283,'Surskit');
INSERT INTO "pokemon" VALUES(284,'Masquerain');
INSERT INTO "pokemon" VALUES(285,'Shroomish');
INSERT INTO "pokemon" VALUES(286,'Breloom');
INSERT INTO "pokemon" VALUES(287,'Slakoth');
INSERT INTO "pokemon" VALUES(288,'Vigoroth');
INSERT INTO "pokemon" VALUES(289,'Slaking');
INSERT INTO "pokemon" VALUES(290,'Nincada');
INSERT INTO "pokemon" VALUES(291,'Ninjask');
INSERT INTO "pokemon" VALUES(292,'Shedinja');
INSERT INTO "pokemon" VALUES(293,'Whismur');
INSERT INTO "pokemon" VALUES(294,'Loudred');
INSERT INTO "pokemon" VALUES(295,'Exploud');
INSERT INTO "pokemon" VALUES(296,'Makuhita');
INSERT INTO "pokemon" VALUES(297,'Hariyama');
INSERT INTO "pokemon" VALUES(298,'Azurill');
INSERT INTO "pokemon" VALUES(299,'Nosepass');
INSERT INTO "pokemon" VALUES(300,'Skitty');
INSERT INTO "pokemon" VALUES(301,'Delcatty');
INSERT INTO "pokemon" VALUES(302,'Sableye');
INSERT INTO "pokemon" VALUES(303,'Mawile');
INSERT INTO "pokemon" VALUES(304,'Aron');
INSERT INTO "pokemon" VALUES(305,'Lairon');
INSERT INTO "pokemon" VALUES(306,'Aggron');
INSERT INTO "pokemon" VALUES(307,'Meditite');
INSERT INTO "pokemon" VALUES(308,'Medicham');
INSERT INTO "pokemon" VALUES(309,'Electrike');
INSERT INTO "pokemon" VALUES(310,'Manectric');
INSERT INTO "pokemon" VALUES(311,'Plusle');
INSERT INTO "pokemon" VALUES(312,'Minun');
INSERT INTO "pokemon" VALUES(313,'Volbeat');
INSERT INTO "pokemon" VALUES(314,'Illumise');
INSERT INTO "pokemon" VALUES(315,'Roselia');
INSERT INTO "pokemon" VALUES(316,'Gulpin');
INSERT INTO "pokemon" VALUES(317,'Swalot');
INSERT INTO "pokemon" VALUES(318,'Carvanha');
INSERT INTO "pokemon" VALUES(319,'Sharpedo');
INSERT INTO "pokemon" VALUES(320,'Wailmer');
INSERT INTO "pokemon" VALUES(321,'Wailord');
INSERT INTO "pokemon" VALUES(322,'Numel');
INSERT INTO "pokemon" VALUES(323,'Camerupt');
INSERT INTO "pokemon" VALUES(324,'Torkoal');
INSERT INTO "pokemon" VALUES(325,'Spoink');
INSERT INTO "pokemon" VALUES(326,'Grumpig');
INSERT INTO "pokemon" VALUES(327,'Spinda');
INSERT INTO "pokemon" VALUES(328,'Trapinch');
INSERT INTO "pokemon" VALUES(329,'Vibrava');
INSERT INTO "pokemon" VALUES(330,'Flygon');
INSERT INTO "pokemon" VALUES(331,'Cacnea');
INSERT INTO "pokemon" VALUES(332,'Cacturne');
INSERT INTO "pokemon" VALUES(333,'Swablu');
INSERT INTO "pokemon" VALUES(334,'Altaria');
INSERT INTO "pokemon" VALUES(335,'Zangoose');
INSERT INTO "pokemon" VALUES(336,'Seviper');
INSERT INTO "pokemon" VALUES(337,'Lunatone');
INSERT INTO "pokemon" VALUES(338,'Solrock');
INSERT INTO "pokemon" VALUES(339,'Barboach');
INSERT INTO "pokemon" VALUES(340,'Whiscash');
INSERT INTO "pokemon" VALUES(341,'Corphish');
INSERT INTO "pokemon" VALUES(342,'Crawdaunt');
INSERT INTO "pokemon" VALUES(343,'Baltoy');
INSERT INTO "pokemon" VALUES(344,'Claydol');
INSERT INTO "pokemon" VALUES(345,'Lileep');
INSERT INTO "pokemon" VALUES(346,'Cradily');
INSERT INTO "pokemon" VALUES(347,'Anorith');
INSERT INTO "pokemon" VALUES(348,'Armaldo');
INSERT INTO "pokemon" VALUES(349,'Feebas');
INSERT INTO "pokemon" VALUES(350,'Milotic');
INSERT INTO "pokemon" VALUES(351,'Castform');
INSERT INTO "pokemon" VALUES(352,'Kecleon');
INSERT INTO "pokemon" VALUES(353,'Shuppet');
INSERT INTO "pokemon" VALUES(354,'Banette');
INSERT INTO "pokemon" VALUES(355,'Duskull');
INSERT INTO "pokemon" VALUES(356,'Dusclops');
INSERT INTO "pokemon" VALUES(357,'Tropius');
INSERT INTO "pokemon" VALUES(358,'Chimecho');
INSERT INTO "pokemon" VALUES(359,'Absol');
INSERT INTO "pokemon" VALUES(360,'Wynaut');
INSERT INTO "pokemon" VALUES(361,'Snorunt');
INSERT INTO "pokemon" VALUES(362,'Glalie');
INSERT INTO "pokemon" VALUES(363,'Spheal');
INSERT INTO "pokemon" VALUES(364,'Sealeo');
INSERT INTO "pokemon" VALUES(365,'Walrein');
INSERT INTO "pokemon" VALUES(366,'Clamperl');
INSERT INTO "pokemon" VALUES(367,'Huntail');
INSERT INTO "pokemon" VALUES(368,'Gorebyss');
INSERT INTO "pokemon" VALUES(369,'Relicanth');
INSERT INTO "pokemon" VALUES(370,'Luvdisc');
INSERT INTO "pokemon" VALUES(371,'Bagon');
INSERT INTO "pokemon" VALUES(372,'Shelgon');
INSERT INTO "pokemon" VALUES(373,'Salamence');
INSERT INTO "pokemon" VALUES(374,'Beldum');
INSERT INTO "pokemon" VALUES(375,'Metang');
INSERT INTO "pokemon" VALUES(376,'Metagross');
INSERT INTO "pokemon" VALUES(377,'Regirock');
INSERT INTO "pokemon" VALUES(378,'Regice');
INSERT INTO "pokemon" VALUES(379,'Registeel');
INSERT INTO "pokemon" VALUES(380,'Latias');
INSERT INTO "pokemon" VALUES(381,'Latios');
INSERT INTO "pokemon" VALUES(382,'Kyogre');
INSERT INTO "pokemon" VALUES(383,'Groudon');
INSERT INTO "pokemon" VALUES(384,'Rayquaza');
INSERT INTO "pokemon" VALUES(385,'Jirachi');
INSERT INTO "pokemon" VALUES(386,'Deoxys');
INSERT INTO "pokemon" VALUES(387,'Turtwig');
INSERT INTO "pokemon" VALUES(388,'Grotle');
INSERT INTO "pokemon" VALUES(389,'Torterra');
INSERT INTO "pokemon" VALUES(390,'Chimchar');
INSERT INTO "pokemon" VALUES(391,'Monferno');
INSERT INTO "pokemon" VALUES(392,'Infernape');
INSERT INTO "pokemon" VALUES(393,'Piplup');
INSERT INTO "pokemon" VALUES(394,'Prinplup');
INSERT INTO "pokemon" VALUES(395,'Empoleon');
INSERT INTO "pokemon" VALUES(396,'Starly');
INSERT INTO "pokemon" VALUES(397,'Staravia');
INSERT INTO "pokemon" VALUES(398,'Staraptor');
INSERT INTO "pokemon" VALUES(399,'Bidoof');
INSERT INTO "pokemon" VALUES(400,'Bibarel');
INSERT INTO "pokemon" VALUES(401,'Kricketot');
INSERT INTO "pokemon" VALUES(402,'Kricketune');
INSERT INTO "pokemon" VALUES(403,'Shinx');
INSERT INTO "pokemon" VALUES(404,'Luxio');
INSERT INTO "pokemon" VALUES(405,'Luxray');
INSERT INTO "pokemon" VALUES(406,'Budew');
INSERT INTO "pokemon" VALUES(407,'Roserade');
INSERT INTO "pokemon" VALUES(408,'Cranidos');
INSERT INTO "pokemon" VALUES(409,'Rampardos');
INSERT INTO "pokemon" VALUES(410,'Shieldon');
INSERT INTO "pokemon" VALUES(411,'Bastiodon');
INSERT INTO "pokemon" VALUES(412,'Burmy');
INSERT INTO "pokemon" VALUES(413,'Wormadam');
INSERT INTO "pokemon" VALUES(414,'Mothim');
INSERT INTO "pokemon" VALUES(415,'Combee');
INSERT INTO "pokemon" VALUES(416,'Vespiquen');
INSERT INTO "pokemon" VALUES(417,'Pachirisu');
INSERT INTO "pokemon" VALUES(418,'Buizel');
INSERT INTO "pokemon" VALUES(419,'Floatzel');
INSERT INTO "pokemon" VALUES(420,'Cherubi');
INSERT INTO "pokemon" VALUES(421,'Cherrim');
INSERT INTO "pokemon" VALUES(422,'Shellos');
INSERT INTO "pokemon" VALUES(423,'Gastrodon');
INSERT INTO "pokemon" VALUES(424,'Ambipom');
INSERT INTO "pokemon" VALUES(425,'Drifloon');
INSERT INTO "pokemon" VALUES(426,'Drifblim');
INSERT INTO "pokemon" VALUES(427,'Buneary');
INSERT INTO "pokemon" VALUES(428,'Lopunny');
INSERT INTO "pokemon" VALUES(429,'Mismagius');
INSERT INTO "pokemon" VALUES(430,'Honchkrow');
INSERT INTO "pokemon" VALUES(431,'Glameow');
INSERT INTO "pokemon" VALUES(432,'Purugly');
INSERT INTO "pokemon" VALUES(433,'Chingling');
INSERT INTO "pokemon" VALUES(434,'Stunky');
INSERT INTO "pokemon" VALUES(435,'Skuntank');
INSERT INTO "pokemon" VALUES(436,'Bronzor');
INSERT INTO "pokemon" VALUES(437,'Bronzong');
INSERT INTO "pokemon" VALUES(438,'Bonsly');
INSERT INTO "pokemon" VALUES(439,'Mime Jr.');
INSERT INTO "pokemon" VALUES(440,'Happiny');
INSERT INTO "pokemon" VALUES(441,'Chatot');
INSERT INTO "pokemon" VALUES(442,'Spiritomb');
INSERT INTO "pokemon" VALUES(443,'Gible');
INSERT INTO "pokemon" VALUES(444,'Gabite');
INSERT INTO "pokemon" VALUES(445,'Garchomp');
INSERT INTO "pokemon" VALUES(446,'Munchlax');
INSERT INTO "pokemon" VALUES(447,'Riolu');
INSERT INTO "pokemon" VALUES(448,'Lucario');
INSERT INTO "pokemon" VALUES(449,'Hippopotas');
INSERT INTO "pokemon" VALUES(450,'Hippowdon');
INSERT INTO "pokemon" VALUES(451,'Skorupi');
INSERT INTO "pokemon" VALUES(452,'Drapion');
INSERT INTO "pokemon" VALUES(453,'Croagunk');
INSERT INTO "pokemon" VALUES(454,'Toxicroak');
INSERT INTO "pokemon" VALUES(455,'Carnivine');
INSERT INTO "pokemon" VALUES(456,'Finneon');
INSERT INTO "pokemon" VALUES(457,'Lumineon');
INSERT INTO "pokemon" VALUES(458,'Mantyke');
INSERT INTO "pokemon" VALUES(459,'Snover');
INSERT INTO "pokemon" VALUES(460,'Abomasnow');
INSERT INTO "pokemon" VALUES(461,'Weavile');
INSERT INTO "pokemon" VALUES(462,'Magnezone');
INSERT INTO "pokemon" VALUES(463,'Lickilicky');
INSERT INTO "pokemon" VALUES(464,'Rhyperior');
INSERT INTO "pokemon" VALUES(465,'Tangrowth');
INSERT INTO "pokemon" VALUES(466,'Electivire');
INSERT INTO "pokemon" VALUES(467,'Magmortar');
INSERT INTO "pokemon" VALUES(468,'Togekiss');
INSERT INTO "pokemon" VALUES(469,'Yanmega');
INSERT INTO "pokemon" VALUES(470,'Leafeon');
INSERT INTO "pokemon" VALUES(471,'Glaceon');
INSERT INTO "pokemon" VALUES(472,'Gliscor');
INSERT INTO "pokemon" VALUES(473,'Mamoswine');
INSERT INTO "pokemon" VALUES(474,'Porygon-Z');
INSERT INTO "pokemon" VALUES(475,'Gallade');
INSERT INTO "pokemon" VALUES(476,'Probopass');
INSERT INTO "pokemon" VALUES(477,'Dusknoir');
INSERT INTO "pokemon" VALUES(478,'Froslass');
INSERT INTO "pokemon" VALUES(479,'Rotom');
INSERT INTO "pokemon" VALUES(480,'Uxie');
INSERT INTO "pokemon" VALUES(481,'Mesprit');
INSERT INTO "pokemon" VALUES(482,'Azelf');
INSERT INTO "pokemon" VALUES(483,'Dialga');
INSERT INTO "pokemon" VALUES(484,'Palkia');
INSERT INTO "pokemon" VALUES(485,'Heatran');
INSERT INTO "pokemon" VALUES(486,'Regigigas');
INSERT INTO "pokemon" VALUES(487,'Giratina');
INSERT INTO "pokemon" VALUES(488,'Cresselia');
INSERT INTO "pokemon" VALUES(489,'Phione');
INSERT INTO "pokemon" VALUES(490,'Manaphy');
INSERT INTO "pokemon" VALUES(491,'Darkrai');
INSERT INTO "pokemon" VALUES(492,'Shaymin');
INSERT INTO "pokemon" VALUES(493,'Arceus');
INSERT INTO "pokemon" VALUES(494,'bikutini');
INSERT INTO "pokemon" VALUES(495,'tsutaaja');
INSERT INTO "pokemon" VALUES(496,'janobii');
INSERT INTO "pokemon" VALUES(497,'jarooda');
INSERT INTO "pokemon" VALUES(498,'pokabu');
INSERT INTO "pokemon" VALUES(499,'chaobuu');
INSERT INTO "pokemon" VALUES(500,'enbuoo');
INSERT INTO "pokemon" VALUES(501,'mijumaru');
INSERT INTO "pokemon" VALUES(502,'futachimaru');
INSERT INTO "pokemon" VALUES(503,'daikenki');
INSERT INTO "pokemon" VALUES(504,'minezumi');
INSERT INTO "pokemon" VALUES(505,'miruhoggu');
INSERT INTO "pokemon" VALUES(506,'yooterii');
INSERT INTO "pokemon" VALUES(507,'haaderia');
INSERT INTO "pokemon" VALUES(508,'muurando');
INSERT INTO "pokemon" VALUES(509,'choroneko');
INSERT INTO "pokemon" VALUES(510,'reparudasu');
INSERT INTO "pokemon" VALUES(511,'yanappu');
INSERT INTO "pokemon" VALUES(512,'yanakkii');
INSERT INTO "pokemon" VALUES(513,'baoppu');
INSERT INTO "pokemon" VALUES(514,'baokkii');
INSERT INTO "pokemon" VALUES(515,'hiyappu');
INSERT INTO "pokemon" VALUES(516,'hiyakkii');
INSERT INTO "pokemon" VALUES(517,'munna');
INSERT INTO "pokemon" VALUES(518,'mushaana');
INSERT INTO "pokemon" VALUES(519,'mamepato');
INSERT INTO "pokemon" VALUES(520,'hatooboo');
INSERT INTO "pokemon" VALUES(521,'kenhorou');
INSERT INTO "pokemon" VALUES(522,'shimama');
INSERT INTO "pokemon" VALUES(523,'zeburaika');
INSERT INTO "pokemon" VALUES(524,'dangoro');
INSERT INTO "pokemon" VALUES(525,'gantoru');
INSERT INTO "pokemon" VALUES(526,'gigaiasu');
INSERT INTO "pokemon" VALUES(527,'koromori');
INSERT INTO "pokemon" VALUES(528,'kokoromori');
INSERT INTO "pokemon" VALUES(529,'moguryuu');
INSERT INTO "pokemon" VALUES(530,'doryuuzu');
INSERT INTO "pokemon" VALUES(531,'tabunne');
INSERT INTO "pokemon" VALUES(532,'dokkoraa');
INSERT INTO "pokemon" VALUES(533,'dotekkotsu');
INSERT INTO "pokemon" VALUES(534,'roobushin');
INSERT INTO "pokemon" VALUES(535,'otamaro');
INSERT INTO "pokemon" VALUES(536,'gamagaru');
INSERT INTO "pokemon" VALUES(537,'gamageroge');
INSERT INTO "pokemon" VALUES(538,'nageki');
INSERT INTO "pokemon" VALUES(539,'dageki');
INSERT INTO "pokemon" VALUES(540,'kurumiru');
INSERT INTO "pokemon" VALUES(541,'kurumayu');
INSERT INTO "pokemon" VALUES(542,'hahakomori');
INSERT INTO "pokemon" VALUES(543,'fushide');
INSERT INTO "pokemon" VALUES(544,'hoiiga');
INSERT INTO "pokemon" VALUES(545,'pendoraa');
INSERT INTO "pokemon" VALUES(546,'monmen');
INSERT INTO "pokemon" VALUES(547,'erufuun');
INSERT INTO "pokemon" VALUES(548,'churine');
INSERT INTO "pokemon" VALUES(549,'doredia');
INSERT INTO "pokemon" VALUES(550,'basurao');
INSERT INTO "pokemon" VALUES(551,'meguroko');
INSERT INTO "pokemon" VALUES(552,'warubiru');
INSERT INTO "pokemon" VALUES(553,'warubiaru');
INSERT INTO "pokemon" VALUES(554,'darumakka');
INSERT INTO "pokemon" VALUES(555,'hihidaruma');
INSERT INTO "pokemon" VALUES(556,'marakacchi');
INSERT INTO "pokemon" VALUES(557,'ishizumai');
INSERT INTO "pokemon" VALUES(558,'iwaparesu');
INSERT INTO "pokemon" VALUES(559,'zuruggu');
INSERT INTO "pokemon" VALUES(560,'zuruzukin');
INSERT INTO "pokemon" VALUES(561,'shinboraa');
INSERT INTO "pokemon" VALUES(562,'desumasu');
INSERT INTO "pokemon" VALUES(563,'desukaan');
INSERT INTO "pokemon" VALUES(564,'purotooga');
INSERT INTO "pokemon" VALUES(565,'abagoora');
INSERT INTO "pokemon" VALUES(566,'aaken');
INSERT INTO "pokemon" VALUES(567,'aakeosu');
INSERT INTO "pokemon" VALUES(568,'yabukuron');
INSERT INTO "pokemon" VALUES(569,'dasutodasu');
INSERT INTO "pokemon" VALUES(570,'zoroa');
INSERT INTO "pokemon" VALUES(571,'zoroaaku');
INSERT INTO "pokemon" VALUES(572,'chiraamy');
INSERT INTO "pokemon" VALUES(573,'chirachiino');
INSERT INTO "pokemon" VALUES(574,'gochimu');
INSERT INTO "pokemon" VALUES(575,'gochimiru');
INSERT INTO "pokemon" VALUES(576,'gochiruzeru');
INSERT INTO "pokemon" VALUES(577,'yuniran');
INSERT INTO "pokemon" VALUES(578,'daburan');
INSERT INTO "pokemon" VALUES(579,'rankurusu');
INSERT INTO "pokemon" VALUES(580,'koaruhii');
INSERT INTO "pokemon" VALUES(581,'suwanna');
INSERT INTO "pokemon" VALUES(582,'banipucchi');
INSERT INTO "pokemon" VALUES(583,'baniricchi');
INSERT INTO "pokemon" VALUES(584,'baibanira');
INSERT INTO "pokemon" VALUES(585,'shikijika');
INSERT INTO "pokemon" VALUES(586,'mebukijika');
INSERT INTO "pokemon" VALUES(587,'emonga');
INSERT INTO "pokemon" VALUES(588,'kaburumo');
INSERT INTO "pokemon" VALUES(589,'shubarugo');
INSERT INTO "pokemon" VALUES(590,'tamagetake');
INSERT INTO "pokemon" VALUES(591,'morobareru');
INSERT INTO "pokemon" VALUES(592,'pururiru');
INSERT INTO "pokemon" VALUES(593,'burungeru');
INSERT INTO "pokemon" VALUES(594,'mamanbou');
INSERT INTO "pokemon" VALUES(595,'bachuru');
INSERT INTO "pokemon" VALUES(596,'denchura');
INSERT INTO "pokemon" VALUES(597,'tesshiido');
INSERT INTO "pokemon" VALUES(598,'nattorei');
INSERT INTO "pokemon" VALUES(599,'giaru');
INSERT INTO "pokemon" VALUES(600,'gigiaru');
INSERT INTO "pokemon" VALUES(601,'gigigiaru');
INSERT INTO "pokemon" VALUES(602,'shibishirasu');
INSERT INTO "pokemon" VALUES(603,'shibibiiru');
INSERT INTO "pokemon" VALUES(604,'shibirudon');
INSERT INTO "pokemon" VALUES(605,'riguree');
INSERT INTO "pokemon" VALUES(606,'oobemu');
INSERT INTO "pokemon" VALUES(607,'hitomoshi');
INSERT INTO "pokemon" VALUES(608,'ranpuraa');
INSERT INTO "pokemon" VALUES(609,'shandera');
INSERT INTO "pokemon" VALUES(610,'kibago');
INSERT INTO "pokemon" VALUES(611,'onondo');
INSERT INTO "pokemon" VALUES(612,'ononokusu');
INSERT INTO "pokemon" VALUES(613,'kumashun');
INSERT INTO "pokemon" VALUES(614,'tsunbeaa');
INSERT INTO "pokemon" VALUES(615,'furiijio');
INSERT INTO "pokemon" VALUES(616,'chobomaki');
INSERT INTO "pokemon" VALUES(617,'agirudaa');
INSERT INTO "pokemon" VALUES(618,'maggyo');
INSERT INTO "pokemon" VALUES(619,'kojofuu');
INSERT INTO "pokemon" VALUES(620,'kojondo');
INSERT INTO "pokemon" VALUES(621,'kurimugan');
INSERT INTO "pokemon" VALUES(622,'gobitto');
INSERT INTO "pokemon" VALUES(623,'goruugu');
INSERT INTO "pokemon" VALUES(624,'komatana');
INSERT INTO "pokemon" VALUES(625,'kirikizan');
INSERT INTO "pokemon" VALUES(626,'baffuron');
INSERT INTO "pokemon" VALUES(627,'washibon');
INSERT INTO "pokemon" VALUES(628,'wooguru');
INSERT INTO "pokemon" VALUES(629,'baruchai');
INSERT INTO "pokemon" VALUES(630,'barujiina');
INSERT INTO "pokemon" VALUES(631,'kuitaran');
INSERT INTO "pokemon" VALUES(632,'aianto');
INSERT INTO "pokemon" VALUES(633,'monozu');
INSERT INTO "pokemon" VALUES(634,'jiheddo');
INSERT INTO "pokemon" VALUES(635,'sazandora');
INSERT INTO "pokemon" VALUES(636,'meraruba');
INSERT INTO "pokemon" VALUES(637,'urugamosu');
INSERT INTO "pokemon" VALUES(638,'kobaruon');
INSERT INTO "pokemon" VALUES(639,'terakion');
INSERT INTO "pokemon" VALUES(640,'birijion');
INSERT INTO "pokemon" VALUES(641,'torunerosu');
INSERT INTO "pokemon" VALUES(642,'borutorosu');
INSERT INTO "pokemon" VALUES(643,'reshiramu');
INSERT INTO "pokemon" VALUES(644,'zekuromu');
INSERT INTO "pokemon" VALUES(645,'randorosu');
INSERT INTO "pokemon" VALUES(646,'kyuremu');
INSERT INTO "pokemon" VALUES(647,'kerudio');
INSERT INTO "pokemon" VALUES(648,'meroetta');
INSERT INTO "pokemon" VALUES(649,'genosekuto');
INSERT INTO "pokemon" VALUES(10001,'Deoxys');
INSERT INTO "pokemon" VALUES(10002,'Deoxys');
INSERT INTO "pokemon" VALUES(10003,'Deoxys');
INSERT INTO "pokemon" VALUES(10004,'Wormadam');
INSERT INTO "pokemon" VALUES(10005,'Wormadam');
INSERT INTO "pokemon" VALUES(10006,'Shaymin');
INSERT INTO "pokemon" VALUES(10007,'Giratina');
INSERT INTO "pokemon" VALUES(10008,'Rotom');
INSERT INTO "pokemon" VALUES(10009,'Rotom');
INSERT INTO "pokemon" VALUES(10010,'Rotom');
INSERT INTO "pokemon" VALUES(10011,'Rotom');
INSERT INTO "pokemon" VALUES(10012,'Rotom');
INSERT INTO "pokemon" VALUES(10013,'Castform');
INSERT INTO "pokemon" VALUES(10014,'Castform');
INSERT INTO "pokemon" VALUES(10015,'Castform');
INSERT INTO "pokemon" VALUES(10016,'basurao');
INSERT INTO "pokemon" VALUES(10017,'hihidaruma');
INSERT INTO "pokemon" VALUES(10018,'meroetta');

COMMIT;
