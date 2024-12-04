# Pathfinder 1E Randomized Character Generator  

## This is a Pathfinder 1E character generator that requires these inputs per character

1) Region
2) Race
3) Class
4) Multi-Class
5) Alignment
6) True Randomization selection for feats
7) Gender
8) Number of stat dice
9) Size of stat dice
10) Highest possible level character
11) Lowest possible level character
12) Starting Gold

Currently, it allows for selection of Pathfinder Base classes + Path of War Base classes

All necessary data has been webscraped from a mix of Archive of Nethys, d20SRD, and library of Metzofitz
- Webscraper code is located in ( Backend/Web Scrapers ) 

When combined with the Frontend pathfinder character sheets (awesome sheet), it becomes a complete character sheet generator for Pathfinder 1E characters.

## Instructions to Run:
To run, you simply need to download the github repository and you can do 1 of 3 things.

1) You can run the main_test.py file to make sure it's running properly on your machine (you will need to install the requirements.txt file first)

2) You can run the app.py file, which will generate a simple HTML / JSON display of all your character data

3) In addition with step 2), you can download the awesome sheet github repository and after following those instructions you should be able to generate sheets on your own servers:
   ( http://localhost:9000/, http://localhost:5000/ )

Pending:
1) Soon, you will be able to visit this website and just click + run there to fulfill all your random character generation needs
https://pathfinder-1e-character-sheet.netlify.app/
2) GPT API call to generate a randomized fully fleshed out character backstory

## More in-depth explanation
What it does:
Randomly generates a complete Pathfinder 1E base character by doing the following:
- The program takes in your 12 inputs (listed above)
- It randomly generates all the data necessary for a Pathfinder 1E character
  ( Age, Height, Weight, Worshipped Deity, Region of origin, Alignment, Character stats, Background traits, Racial traits, Ability Mods, Randomized Character Flaws, Level, Hit points, Spell lists based off of selected class (With exclusions based off of Alignment), Feat lists (Truly Random or Buckets appropriate for class), Extra feats (depending on class + race), Languages known, Randomly assigned skill ranks, Random professions, favored class options, Selected Domains, Selected Class abilities ( Rage powers, arcanist exploits, discoveries, rogue talents, wizard school, bloodlines, domains, mercies, cruelties, favored terrains, favored enemies, ... ), Random Magic Items, Armor/Shield Selection, Weapon Selection, Armor/Shield/Weapon Enhancements, Appearance (hair color, hair type, eye color), Mannerisms, Hero Points )
- This data is generated as JSON data
- The data is sent onto a FLASK server on ( http://localhost:9000/ )
- Communication between ( http://localhost:5000/ ) is opened to allow for better frontend experience
Example:
![image](https://github.com/The-Data-is-a-lie/Pathfinder_Char_Creator/assets/129898955/eeed6327-5630-4bed-b3f7-f3aac8db7fe7)


## Custom Functions used in the program located in:
- Utils/
- Utils/class_func

## Webscraped data located in:
- json
- json/class_data
- json/class_data/path_of_war

## HTML files located in:
- templates

## csv data files located in:
- data
- data/archetype_csv

In the Works:
- Spheres of Power / Might (classes + abilities + archetypes )
- Fully Flesh out Path of War
- Homebrew feats / races ( Feats + Races that I use in my Pathfinder 1E games)
- Mythic

- Download the Files or Clone the Repo from here [main.py](https://github.com/Daniel-Grkinich/Pathfinder_Char_Creator.git)  

## Contact
Please contact me at tapletopsoftware@gmail.com if you have any questions regarding this. My dream is to make this an open-source website that anyone can use to play pathfinder 1e more easily.

## Requirements
 - Python (>= 3.10)
