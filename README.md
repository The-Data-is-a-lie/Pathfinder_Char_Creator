# Pathfinder 1E Randomized Character Generator  
Hello everyone. This is a module I created to randomly generate (mostly) Paizo official rules following Pathfinder 1E characters. This is the Backend portion created mostly in Python to utilize it to it's fullest potential, you can combine this with the add-on module I created for the FoundryVTT app (link: https://foundryvtt.com/packages/pf1e-random-char-generator) and it will generate a fully functioning character sheets within seconds.  

It works by taking in a set of inputs (see below screenshot) from FoundryVTT and generates a character sheet (in JSON data) then sends it back over where it is used to fill in a character sheet.

<img width="429" height="687" alt="image" src="https://github.com/user-attachments/assets/d2fa6c93-8cf0-4ff1-8270-7d91f650c27f" />

Detailed list of what each button does:
https://gitlab.com/pathfinder_1e_randomized_character_generator/FoundryVTT_Random_Pf1e_Char_Generator/-/wikis/How-to-use

All necessary data have been webscraped from a mix of Archive of Nethys, d20SRD, and library of Metzofitz.

**Future Additions:**
- Working on Path of War
- Spheres of Power
- If you want something added, please contact me via my info below

**Cool things I did:**
- Used a Docker to generate a Docker image -> creating your own backend is a copy + paste process (link below)
- In case something happens to the usual sources of information, I have scraped 10K+ links to gather nearly all possible Pathfinder information involved in generating a character (including race, classes, items, weapons, armor, domains, deities, ... )


**Links Section:**

How to set up your backend:
https://gitlab.com/pathfinder_1e_randomized_character_generator/FoundryVTT_Random_Pf1e_Char_Generator/-/wikis/home

How it works:
https://gitlab.com/pathfinder_1e_randomized_character_generator/FoundryVTT_Random_Pf1e_Char_Generator/-/wikis/How-it-works

How to use:
https://gitlab.com/pathfinder_1e_randomized_character_generator/FoundryVTT_Random_Pf1e_Char_Generator/-/wikis/How-to-use

Known Bug Fixes:
https://gitlab.com/pathfinder_1e_randomized_character_generator/FoundryVTT_Random_Pf1e_Char_Generator/-/wikis/How-to-Bug-Fix

Current Backend (Only works when communicating with the Frontend):
https://pathfinder-char-creator-web-public-use.onrender.com

FoundryVTT module Download location:
https://foundryvtt.com/packages/pf1e-random-char-generator

FoundryVTT module instructions:
https://gitlab.com/pathfinder_1e_randomized_character_generator/FoundryVTT_Random_Pf1e_Char_Generator/-/wikis/home

Contact me:
tabletopsoftware@gmail.com
