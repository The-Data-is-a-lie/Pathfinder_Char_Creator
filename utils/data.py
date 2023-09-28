#Only small amounts of data, we don't want to have massive 1000+ lines long of data here

# where you want characters to be from:
skills = ["Acrobatics",
"Appraise",
"Bluff",
"Climb",
"Craft",
"Diplomacy",
"Disable Device",
"Disguise",
"Escape Artist",
"Fly",
"Gather Information",
"Handle Animal",
"Heal",
"Intimidate",
"Knowledge (Arcana)",
"Knowledge (Dungeoneering)",
"Knowledge (Engineering)",
"Knowledge (Geography)",
"Knowledge (History)",
"Knowledge (Local)",
"Knowledge (Nature)",
"Knowledge (Martial)",
"Knowledge (Nobility)",
"Knowledge (Planes)",
"Knowledge (Religion)",
"Linguistics",
"Perception",
"Perform",
"Profession",
"Ride",
"Sense Motive",
"Sleight of Hand",
"Spellcraft",
"Stealth",
"Survival",
"Swim",
"Use Magic Device",
"Artistry",
"Profession",
"Lore"]

#must match the same order as the weapon_groups_region section
regions = ["Tal-falko","Dolestan","Sojoria","Ieso", "Spire", "Feyador", "Esterdragon", "Grundy", "Dust-Cairn", "Kaeru no Tochi"]
races = ["Human", "Aasimar", "Catfolk", "Dragonborn", "Dhampir", "Drow", "Duergar", "Elf", "Fetchling", "Goblin", "Gnome", "Halfling", "Dwarf", "Half-elf", "Half-orc", "Hobgoblin", "Ifrit", "Kitsune", "Kobold", "Monkey Goblin", "Orc", "Oread", "Ratfolk", "Sylph", "Tengu", "Tiefling", "Undine", "Wayang", "Loxophant", "D-ziriak", "Tortugan"]
weapon_groups = ['Axes', 'Blades, Heavy', 'Blades, Light', 'Bows', 'Close', 'Crossbows', 'Double', 'Firearms', 'Flails', 'Hammers', 'Monk', 'Natural', 'Polearms', 'Siege Engines', 'Spears', 'Thrown', 'Tribal']

# make weapon group into a dictionary that depends on regions:
weapon_groups_region = {
    'Tal-falko': ['Swords', 'Axes', 'Bows'],
    'Dolestan': ['Maces', 'Spears', 'Wands'],
    'Sojoria': ['Swords', 'Bows', 'Wands'],
    'Ieso': ['Axes', 'Maces', 'Spears'],
    'Spire': ["Greathammer", "Starknife", "Flail", "Scythe", "Dagger", "Shortsword" ],
    'Feyador': ['Bow', 'Spear'],
    'Esterdragon': ['Polearm','Staff'],
    'Grundy': ['Sling', 'Club'],
    'Dust-Cairn': ['Spear','Natural Weapon', 'Lance', 'Greatsword', 'Rapier'],
    'Kaeru no Tochi': ['katana', 'Kusarigama', 'Tonfa', 'Hooked Lance', 'Nodachi', 'Kama', 'Wakizashi']
}

hit_dice = {
    "d12": ["Barbarian", "Warder"],
    "d10": ["Anti-Paladin","Bloodrager","Brawler","Fighter","Cavalier","Gunslinger","Paladin","Ranger","Samurai","Slayer","Swashbuckler", "Unchained Monk", "Warlord","Zealot"],
    "d8": ["Alchemist","Bard","Cleric","Druid","Hunter","Inquisitor","Investigator","Magus","Medium","Mesmerist","Mystic","Ninja","Occultist","Oracle","Psychic","Rogue","Shaman","Skald","Spiritualist","Summoner","Stalker","Warpriest"],
    "d6": ["Arcanist","Psychic","Sorcerer","Witch","Wizard"]
}

#add all of forests options
languages = ['Abyssal', 'Aklo', 'Aquan', 'Auran', 'Boggard', 'Celestial', 'Common', 'Cyclops', 'Dark Folk', 'Draconic', 'Drow Sign Language', 'Dwarven', 'Elven', 'Giant', 'Gnoll', 'Gnome', 'Goblin', 'Grippli', 'Halfling', 'Ignan', 'Infernal', 'Kelish', 'Orc', 'Protean', 'Sphinx', 'Sylvan', 'Tengu', 'Terran', 'Treant', 'Undercommon', 'Vegepygmy', 'Vishkanya', 'Wayang']
#add all of forests options
good_deities = [ "Abadar",    "Cayden Cailean",    "Desna",    "Erastil",    "Iomedae",    "Irori",    "Sarenrae",    "Shelyn",    "Torag",    "Amaznen",    "Angradd",    "Apsu",    "Chaldira Zuzaristan",    "Chamidu",    "Chevaghol",    "Dorasharn",    "Eritrice",    "Falayna",    "Ghenshau",    "Green Faith",    "Gruhastha",    "Hathor",    "Hei Feng",    "Horus",    "Kofusachi",    "Kurgess",    "Lady Nanbyo",    "Lysianassa",    "Milani",    "Nalinivati",    "Nethys",    "Norgorber",    "Osiris",    "Pharasma",    "Qi Zhong",    "Ragdya",    "Razmir",    "Sivanah",    "Spirits of the Land",    "Sulak",    "Sun Wukong",    "Tsukiyo",    "Wadjet",    "Yamatsumi",    "Ydersius",    "Zon-Kuthon"]
neutral_deities = ["Apsu",
"Aroden",
"Besmara",
"Brigh",
"Calistria",
"Cayden Cailean",
"Desna",
"Erastil",
"Ghlaunder",
"Gozreh",
"Grandmother Spider",
"Groteus",
"Iomedae",
"Irori",
"Lamashtu",
"Nethys",
"Norgorber",
"Pharasma",
"Qi Zhong",
"Sarenrae",
"Shelyn",
"Torag",
"Urgathoa",
"Wadjet",
"Ydersius",
"Zyphus"]
evil_deities = ["Asmodeus",
"Baphomet",
"Dahak",
"Droskar",
"Ghlaunder",
"Gorum",
"Groetus",
"Lamashtu",
"Norgorber",
"Rovagug",
"Szuriel",
"Urgathoa",
"Zon-Kuthon"]
#all_deities = ['Abadar', 'Achaekek', 'Alseta', 'Ameiko Kaijitsu', 'Apsu', 'Aroden', 'Asmodeus', 'Black Butterfly, The', 'Brigh', 'Calistria', 'Cayden Cailean', 'Chaldira Zuzaristan', 'Chamidu', 'Daikitsu', 'Dahak', 'Desna', 'Elion', 'Erastil', 'Ghlaunder', 'Gorum', 'Gozreh', 'Groetus', 'Gruhastha, The', 'Hanspur', 'Hei Feng', 'Iomedae', 'Irori', 'Jaidi', 'Jingxi', 'Kabriri', 'Kazutal', 'Kelizandri', 'Ketephys', 'Kofusachi', 'Lama, The', 'Lamashtu', 'Magrim', 'Milani', 'Minderhal', 'Naderi', 'Nalinivati', 'Nethys', 'Nivi Rhombodazzle', 'Norgorber', 'Old-Mage Jatembe', 'Oras', 'Orcus', 'Pharasma', 'Qi Zhong', 'Ragathiel', 'Razmir', 'Rovagug', 'Sarenrae', 'Sivanah', 'Sivanah, The', 'Skrymir', 'Sokhna', 'Sun Wukong', 'Thamir Gixx', 'Thremyr', 'Torag', 'Urgathoa', 'Uskyeria', 'Wadjet', 'Weydan', 'Ydersius', 'Yuelral', 'Zagnexapan', 'Zargos', 'Zon-Kuthon' ]
alignment = ["Chaotic good", "Chaotic neutral", "Chaotic evil", "Lawful good", "Lawful neutral", "Lawful evil", "Neutral good", "True Neutral", "Neutral evil"]

hair_colors = ['Black', 'Brown', 'Blond', 'Red', 'White', 'Grey']
hair_types = ['Curly', 'Wavy', 'Straight', 'Flowing', 'Frizzy', 'Spiky', 'Touseled', 'Unkempt','Bald']
eye_colors = ['Amber', 'Blue', 'Brown', 'Grey', 'Green', 'Hazel']
appearance = [  "Athletic",
  "Bald",
  "Beautiful",
  "Beefy",
  "Big-boned",
  "Blemished",
  "Blonde",
  "Blue-eyed",
  "Blushing",
  "Bony",
  "Bow-legged",
  "Braided hair",
  "Broken nose",
  "Brunette",
  "Bulging eyes",
  "Bushy eyebrows",
  "Butterfly tattoo",
  "Chubby",
  "Clean-shaven",
  "Clumsy",
  "Colored hair",
  "Confident",
  "Cross-eyed",
  "Curly hair",
  "Dapper",
  "Dark-skinned",
  "Dazzling",
  "Defined cheekbones",
  "Delicate",
  "Dimpled",
  "Dirty",
  "Distinguished",
  "Double chin",
  "Droopy eyes",
  "Dumpy",
  "Elegant",
  "Emaciated",
  "Energetic",
  "Enthusiastic",
  "Exotic",
  "Exquisite",
  "Fierce",
  "Fiery",
  "Filthy",
  "Fine hair",
  "Flabby",
  "Flat nose",
  "Flawless skin",
  "Freckled",
  "Friendly",
  "Frizzy hair",
  "Full lips",
  "Gangly",
  "Gap-toothed",
  "Gelled hair",
  "Geometric tattoo",
  "Glamorous",
  "Gleaming",
  "Glistening",
  "Glossy hair",
  "Gorgeous",
  "Graceful",
  "Grinning",
  "Grimacing",
  "Grizzled",
  "Hairy",
  "Handsome",
  "Happy",
  "Harmonious",
  "Harsh",
  "Hazel-eyed",
  "Healthy",
  "Heart-shaped face",
  "Hefty",
  "Henna tattoo",
  "Hollow cheeks",
  "Homely",
  "Honey-colored eyes",
  "Hooded eyes",
  "Huge ears",
  "Hunched",
  "Husky",
  "Icy blue eyes",
  "Impish",
  "Infectious smile",
  "Intricate tattoos",
  "Jagged scar",
  "Jaunty",
  "Jaw-dropping",
  "Jowly",
  "Juicy lips",
  "Keen-eyed",
  "Knobby knees",
  "Lanky",
  "Large forehead",
  "Large nose",
  "Laughing eyes",
  "Lean",
  "Leathered skin",
  "Leggy",
  "Lethargic",
  "Light hair",
  "Lithe",
  "Lively",
  "Lopsided smile",
  "Loud",
  "Lovely",
  "Luminous",
  "Lumpy",
  "Luscious",
  "Madcap",
  "Majestic",
  "Manicured nails",
  "Masculine",
  "Meaty",
  "Melancholy",
  "Mellow",
  "Messy hair",
  "Mighty",
  "Mild",
  "Mirthful",
  "Mischievous",
  "Missing teeth",
  "Mohawk",
  "Muscular",
  "Narrow-eyed",
  "Natural beauty",
  "Neat",
  "Nervous",
  "Noble",
  "Nose ring",
  "Oily skin",
  "Old-fashioned",
  "Open",
  "Overweight",
  "Pallid",
  "Pensive",
  "Perky",
  "Piercings",
  "Pimply",
  "Plain",
  "Plump",
  "Polished",
  "Ponytail",
  "Portly",
  "Posh",
  "Pot-bellied",
  "Pouty lips",
  "Pretty",
  "Prim",
  "Protruding ears",
  "Pudgy",
  "Puffy eyes",
  "Ragged",
  "Rakish",
  "Raspy voice",
  "Ravishing",
  "Receding hairline",
  "Refined",
  "Regal",
  "Ripped",
  "Rough hands",
  "Ruddy complexion",
  "Rugged",
  "Runny nose",
  "Sad",
  "Sallow",
  "Salt-and-pepper hair",
  "Sassy",
  "Scrawny",
  "Scruffy",
  "Sculpted",
  "Seductive",
  "Self-assured",
  "Sensitive",
  "Serene",
  "Sexy",
  "Shapely",
  "Sharp features",
  "Shaved head",
  "Shifty eyes",
  "Shimmering eyes",
  "Shiny hair",
  "Short",
  "Shy",
  "Sickly",
  "Skeletal",
  "Skinny",
  "Sleek",
  "Sloppy",
  "Small eyes",
  "Smiling",
  "Smooth skin",
  "Snaggletooth",
  "Snazzy",
  "Sneering",
  "Snub nose",
  "Soft-spoken",
  "Solid",
  "Soothing voice",
  "Spectacled",
  "Spiky hair",
  "Spindly",
  "Spirited",
  "Square jaw",
  "Squat",
  "Stately",
  "Stocky",
  "Striking",
  "Stubbled",
  "Studious",
  "Stunning",
  "Stylish",
  "Sun-kissed skin",
  "Sunburned",
  "Supple",
  "Svelte",
  "Swaggering",
  "Sweaty",
  "Sweet",
  "Symmetrical",
  "Tall",
  "Tanned",
  "Tattoos",
  "Teasing",
  "Teeth gap",
  "Tense",
  "Thin",
  "Thinning hair",
  "Thick eyebrows",
  "Thick lips",
  "Thick-rimmed glasses",
  "Thoughtful",
  "Throaty voice",
  "Thunder thighs",
  "Tight-lipped",
  "Tiny",
  "Tired",
  "Toothy grin",
  "Tousled hair",
  "Towering"]

#Combat Spheres:
combat_spheres = ["Alchemy","Athletics","Barrage","Barroom","Beastmastery","Berserker","Boxing","Brute","Dual Wielding","Duelist","Equipment","Fencing","Gladiator","Guardian","Lancer","Open Hand","Scoundrel","Scout","Shield","Sniper","Trap","Warleader","Wrestling"]
#magic spheres:
magic_spheres = ["Alteration","Blood","Conjuration","Creation","Dark","Death","Destruction","Divination","Enhancement","Fallen Fey","Fate","Illusion","Life","Light","Mana","Mind","Nature","Protection","Telekinesis","Time","War","Warp","Weather"]
#skill spheres:
skill_spheres = ["Artifice", "Bluster", "Body Control", "Communication", "Faction", "Herbalism", "Infiltration", "Investigation", "Navigation", "Performance", "Spellhacking", "Study", "Subterfuge", "Survivalism", "Vocation"]

#path of war classes:
path_of_war_class = ['Warder', 'Harbinger', 'Mystic', 'Zealot', 'Stalker']

#add all of forests options


#add all of forests options

#add all of forests options
mannerisms = ['Adjusts glasses', 'Bites fingernails', 'Bites lip', 'Blows bubbles', 'Brushes hair out of face', 'Bursts into laughter', 'Chews gum', 'Chuckles', 'Clicks pen', 'Clutches purse tightly', 'Combs hair with fingers', 'Covers mouth when speaking', 'Cracks knuckles', 'Crosses arms', 'Crosses legs', 'Curls up in a ball', 'Doodles', 'Drums fingers', 'Eyes dart around room', 'Fiddles with hair', 'Fidgets', 'Flexes muscles', 'Folds arms', 'Furrows brow', 'Gestures while talking', 'Glances at watch', 'Grins', 'Hides hands in pockets', 'Hugs oneself', 'Hums to oneself', 'Jingles keys', 'Jumps up and down', 'Laughs at own jokes', 'Leans back', 'Leans forward', 'Licks lips', 'Lifts eyebrows', 'Lifts chin', 'Licks teeth', 'Looks around nervously', 'Looks over glasses', 'Mumbles', 'Nervously clears throat', 'Nods often', 'Opens and closes mouth', 'Paces', 'Pats pockets', 'Peers over glasses', 'Plays with jewelry', 'Plays with sleeves', 'Pops knuckles', 'Puts hands in pockets', 'Raises eyebrows', 'Readjusts clothing', 'Rests chin in hand', 'Rests hand on hip', 'Rests head on hand', 'Rolls eyes', 'Rub hands together', 'Runs fingers through hair', 'Scratches head', 'Shakes head', 'Shifts weight from one foot to the other', 'Shrugs', 'Sighs', 'Smacks lips', 'Smiles', 'Smirks', 'Snaps fingers', 'Squints', 'Stares into space', 'Stares intensely', 'Stifles a yawn', 'Strokes chin', 'Sways back and forth', 'Sweats', 'Swings arms', 'Taps foot', 'Taps pencil', 'Thumbs through a book', 'Throws head back when laughing', 'Tilts head', 'Tucks hair behind ears', 'Twiddles thumbs', 'Twirls hair', 'Twists hair', 'Twitches', 'Winks', 'Wipes hands on pants', 'Wipes nose', 'Wipes sweat from forehead', 'Withdraws into oneself', 'Wring hands', 'Yawns', 'Yells when excited', 'Zones out', 'Bites lower lip', 'Bites upper lip', 'Blows nose', 'Brushes off clothes', 'Clenches fists', 'Clenches jaw', 'Combs mustache', 'Covers ears', 'Covers eyes', 'Crosses fingers', 'Crouches', 'Cups chin with hand', 'Dabs at eyes', 'Dons sunglasses', 'Drops head', 'Elevates eyebrows', 'Exhales audibly', 'Fans oneself', 'Fiddles with jewelry', 'Fingers lapel', 'Flips hair', 'Folds hands', 'Gathers hair into a ponytail', 'Glances away', 'Glances over shoulder', 'Gnaws on pencil', 'Grits teeth', 'Holds breath', 'Huffs', 'Jumps at sudden sounds', 'Kicks at the ground', 'Kneads fingers', 'Kneels', 'Lays head on desk', 'Leans on desk', 'Lift']

#add all of forests options
traits = ['ambitious', 'anxious', 'artistic', 'brave', 'calm', 'careless','charming', 'clever', 'compassionate', 'confident', 'creative','curious', 'daring', 'dependable', 'determined', 'discreet','distrustful', 'eccentric', 'emotional', 'energetic', 'enthusiastic','ethical', 'excitable', 'friendly', 'frustrated', 'generous','gloomy', 'graceful', 'grateful', 'gregarious', 'guarded', 'happy','hardworking', 'honest', 'humorous', 'imaginative', 'impatient','indecisive', 'independent', 'industrious', 'inquisitive', 'intelligent','introverted', 'kind', 'knowledgeable', 'logical', 'loyal', 'mature','methodical', 'modest', 'moody', 'naive', 'narcissistic', 'neurotic','optimistic', 'organized', 'outgoing', 'paranoid', 'passionate', 'patient','perfectionist', 'persistent', 'pessimistic', 'philosophical', 'playful','polite', 'practical', 'proactive', 'proud', 'quiet', 'quick-tempered','rational', 'reliable', 'reserved', 'resourceful', 'restless', 'romantic','sensitive', 'serious', 'shy', 'skeptical', 'sociable', 'solitary','spontaneous', 'stubborn', 'studious', 'submissive', 'suspicious','talkative', 'temperamental', 'thoughtful', 'thrifty', 'tolerant','trustworthy', 'unselfish', 'unstable', 'vain', 'virtuous', 'warmhearted','wary', 'witty', 
              'Adventurous', 'Affectionate', 'Aggressive', 'Analytical', 'Assertive', 'Cautious', 'Charismatic', 'Charming', 'Clever', 'Comical', 'Compassionate', 'Confident', 'Conservative', 'Considerate', 'Courageous', 'Cynical', 'Dependable', 'Determined', 'Devoted', 'Eccentric', 'Empathetic', 'Energetic', 'Enthusiastic', 'Excitable', 'Extroverted', 'Friendly', 'Gregarious', 'Hardworking', 'Idealistic', 'Innovative', 'Insightful', 'Intelligent', 'Intuitive', 'Inventive', 'Inquisitive', 'Jovial', 'Loyal', 'Meticulous', 'Mysterious', 'Objective', 'Observant', 'Optimistic', 'Organized', 'Outgoing', 'Passionate', 'Patient', 'Perfectionist', 'Persistent', 'Pessimistic', 'Practical', 'Protective', 'Rational', 'Realistic', 'Reliable', 'Reserved', 'Resourceful', 'Respectful', 'Responsible', 'Risk-taking', 'Romantic', 'Sarcastic', 'Skeptical', 'Sociable', 'Spontaneous', 'Stoic', 'Straightforward', 'Stubborn', 'Sympathetic', 'Tactful', 'Tenacious', 'Thoughtful', 'Trusting', 'Unconventional', 'Understanding', 'Unselfish', 'Vigilant', 'Visionary', 'Warm', 'Witty', 'Zealous']

#add all of forests options

# Comprehensive list of Archetypes:
#need to use archetypes_{class_name} so we can grab it like this later
                    #Base Classes

disciplines = ['Black Seraph', 'Broken Blade', 'Brutal Crocodile', 'Cursed Razor', 'Elemental Flux', 'Eternal Guardian', 'Fools Errand', 'Golden Lion', 'Iron Tortoise', 'Leaden Hyena', 'Mangled Gear', 'Mithral Current', 'Piercing Thunder', 'Primal Fury', 'Radiant Dawn', 'Riven Hourglass', 'Roaring Mouse', 'Sagitta Stellaris', 'Scarlet Throne', 'Shattered Mirror', 'Silver Crane', 'Sleeping Goddess', 'Solar Wind', 'Spark of Battle', 'Steel Serpent', 'Surging Shark', 'Tempest Gale', 'Thrashing Dragon', 'Unquiet Grave', 'Veiled Moon']

                    #Path of war classes

version = "4/30/23"
