pokemon-encounters - Collection of scripts for dumping Pokémon encounter data.

And also importing said data into [Veekun][] (eventually).

[Veekun]: http://veekun.com/

GPL licensed. Except `db.py` and `nds/narc.py`, which are from
<http://git.veekun.com/pokedex.git> and are MIT-licensed.

The data is owned by Nintendo and Game Freak.


Overview
--------

This is a three-step process. Basically, it goes
ROM
 => binary format
 => textual format
 => database.

1. First we extract the data from the ROM. The NDS games store the data in
   a structured format already, so this is extracted with a tool such as
   [porigon-z][] and used directly. For earlier games, the data is extracted
   and stored in a binary format which is as similar to the original data as
   possible.

   The data dumps are located in `data/`.

   The ROMs themselves cannot be included, for obvious reasons.

2. The next step is to transform the game-specific data into a readable,
   generic format. Currently this is an XML format, though i'm not sure why
   i don't use JSON, given that the first step in the importer

   The data should still be structured like it is in the actual game.

3. The importer. There is (hopefully only one) importer which reads the 
   generic format and imports the data into the database.

   The importer is responsible for molding the data into the specific 
   structure of the database. For Veekun's database, this means a ton
   of normalization.

[porigon-z]: http://bugs.veekun.com/projects/porigon-z
