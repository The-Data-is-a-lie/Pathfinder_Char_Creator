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
races = ["Human", "Aasimar", "Catfolk", "Dragonborn", "Dhampir", "Drow", "Duergar", "Elf", "Fetchling", "Goblin", "Gnome", "Halfling", "Dwarf", "Half-Elf", "Half-Orc", "Hobgoblin", "Ifrit", "Kitsune", "Kobold", "Monkey Goblin", "Orc", "Oread", "Ratfolk", "Sylph", "Tengu", "Tiefling", "Undine", "Wayang", "Loxophant", "D-ziriak", "Tortugan"]
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

#all base classes are done
archetypes = {
'alchemist': ['base',"Metallurgist (Alchemist Archetype)", "Necrophage (Ghoul Alchemist Archetype)", "Mutator (Blue)", "Metallurgist", "Mutator", "Wild Experimenter", "Fumigant", "Moonshiner", "Lycanthologist", "Herbalist", "Perfumer", "Cruorchymist (Alchemist Archetype)", "Aerochemist", "Mixologist", "Mnemostiller", "Energist", "Blightseeker", "Bogborn", "Bramble Brewer (Half-elf)", "Deep Bomber (Svirfneblin)", "Fey World Innovator", "Fire Bomber", "Oenopion Researcher", "Oozemaster", "Plague Bringer", "Saboteur", "Vaultbreaker", "Concocter", "Fermenter", "Gun Chemist", "Ice Chemist", "Aquachymist", "Crimson Chymist", "Energy Scientist", "Reanimator", "Royal Alchemist", "Sacrament Alchemist", "Wasteland Blighter", "Tinkerer", "Alchemical Sapper", "Alchemical Trapper (Kobold)", "Beastmorph", "Blazing Torchbearer", "Blood Alchemist", "Chirurgeon", "Clone Master", "Construct Rider", "Crypt Breaker", "Dimensional Excavator", "Dragonblood Chymist", "Ectochymist", "Ectoplasm Master", "Eldritch Poisoner", "Gloom Chymist", "Grenadier (PFS Field Guide)", "Grenadier (PRG:MC)", "Homunculist", "Horticulturist", "Inspired Chemist", "Internal Alchemist", "Interrogator", "Mad Scientist", "Metamorph", "Mindchemist", "Preservationist", "Promethean Alchemist", "Psychonaut", "Ragechemist", "Toxicant", "Trap Breaker", "Visionary Researcher", "Vivisectionist", "Winged Marauder (Goblin)"]
#*
,
'anti-paladin': ['base',"Kinetic Despoiler","Midnight Gun","Sinsworn Reaver","Spectral Terror","Witch-Eyed Knight","Blighted Myrmidon","Dread Vanguard","Fearmonger","Insinuator","Iron Tyrant","Knight of the Sepulcher","Rampager","Seal-Breaker","Tyrant"]
#*
,
'arcanist': ['base',"Arcane Tinkerer","Aeromancer","Blade Adept","Blood Arcanist","Brown-Fur Transmuter","Collegiate Initiate","Eldritch Font","Elemental Master","Occultist","School Savant","Spell Specialist","Tarot Student","Twilight Sage","Unlettered Arcanist","White Mage"]
#*
,
'barbarian': ['base','Armored Hulk','Beastkin Berserker',"Brutish Swamper","Cave Dweller","Deepwater Rager","Giant Stalker","Pack Hunter","Sharptooth","Wildborn","Geminate Invoker","Armored Hulk","Breaker","Brutal Pugilist","Burn Rider","Dreadnought","Drunken Brute","Drunken Rager","Elemental Kin","Fearsome Defender","Flesheater","Hurler","Invulnerable Rager","Jungle Rager","Liberator","Mad Dog","Mooncursed","Mounted Fury","Pack Rager","Primal Hunter","Raging Cannibal","Savage Barbarian","Savage Technologist","Scarred Rager","Sea Reaver","Superstitious","Titan Mauler","Totem Warrior","True Primitive","Untamed Rager","Urban Barbarian","Wild Rager"]
,
#*
'bard': ['base',"Speaker of the Palatine Eye","Clockspeaker","Dwarven Scholar","Chronicler of Worlds","Cultivator","Disciple of the Forked Tongue (Vishkanya)","Fey Courtier","Fey Prankster","Fey World Minstrel","Filidh","Fortune-Teller","Luring Piper","Plant Speaker","Stonesinger","Thundercaller (PRG:UW)","Wasteland Chronicler","Argent Voice","Brazen Deceiver","Flamesinger","Ringleader (PRG:AG)","Flame Dancer","Diva","Animal Speaker","Arbiter","Arcane Duelist","Arcane Healer","Archaeologist","Archivist","Arrowsong Minstrel","Buccaneer","Busker","Celebrity","Court Bard","Court Fool","Daredevil","Demagogue","Dervish Dancer","Dervish of Dawn","Detective","Dirge Bard","Dragon Yapper (Kobold)","Duettist","Faith Singer","Geisha","Hoaxer","Impervious Messenger","Juggler","Lotus Geisha","Magician","Masked Performer","Mute Musician","Negotiator","Phrenologist","Provocateur","Ringleader (PRG:UI)","Sandman","Savage Skald","Sea Singer","Silver Balladeer","Solacer","Songhealer","Sorrowsoul","Sound Striker","Street Performer","Studious Librarian","Thundercaller (PPC:VBL)","Voice of the Wild","Wit"]
#*
,
'bloodrager': ['base',"Symbol Striker","Ancestral Harbinger","Blood Conduit","Bloodrider","Bloody-Knuckled Rowdy","Crossblooded Rager","Enlightened Bloodrager (PZO1138)","Enlightened Bloodrager (PZO9465)","Greenrager","Hag-Riven","Id Rager","Metamagic Rager","Primalist","Prowler at World's End","Rageshaper","Spelleater","Steelblood","Untouchable Rager","Urban Bloodrager"]
#*
,
'brawler': ['base',"Battle Dancer (Brawler Archetype)","Beast-Wrestler","Bouncer","Constructed Pugilist","Exemplar","Feral Striker","Hinyasi","Living Avalanche","Mutagenic Mauler","Shield Champion","Snakebite Striker","Steel-Breaker","Strangler","Strong-Side Boxer (Brawler Archetype)","Turfer","Venomfist","Verdant Grappler","Wild Child","Winding Path Renegade"]
#*
,
'cleric': ['base',"Angakok" "Talvikind" "Cultist" "DivineAnimalCompanion" "DivineEnergy" "ShadowPriest" "UnholyBarrister" "Avatar" "SteelValkyrie" "DiscipleofOrcus" "Filth-PriestofTsathogga" "Polyglot" "Wuuntzu" "CultistofCharun" "Ascetic" "Charismatic" "Enthusiast" "Exorcist" "Flagelant" "Theosophist" "Vatic" "Weapon-Sworn" "WonderWorker" "Lawspeaker" "Idealist" "ChanneleroftheUnknown" "TriadicPriest" "BlossomingLight" "CrashingWave" "FoundationofFaith" "AsmodeanAdvocate" "Cardinal" "AngelfireApostle" "Appeaser" "CloisteredCleric" "Crusader" "DevilbanePriest" "DevoutPilgrim" "DivineParagon" "DivineScourge" "DivineStrategist" "Ecclesitheurge" "ElderMythosCultist" "Evangelist" "HeraldCaller" "HiddenPriest" "IronPriest" "MercifulHealer" "RoamingExorcist" "SacredAttendant" "ScrollScholar" "Separatist" "StoicCaregiver" "Theologian" "UndeadLord" "OccultPriest" "Kappa-Kannushi" "PiousSentinel" "Idolater"]
,
#*
'cavalier': ['base',"Fell Rider (Hobgoblin)","Outrider (Lashunta)","Castellan","Circuit Judge","Constable","Courtly Knight","Daring Champion","Daring General","Disciple of the Pike","Drake Rider","Dune Drifter","Emissary","Esquire","Gallant","Gendarme","Ghost Rider","Green Knight","Herald Squire","Honor Guard","Horselord","Huntmaster","Hussar","Knight of the Wall","Luring Cavalier","Mother’s Fang","Musketeer","Oceanrider","Saurian Champion","Sister in Arms","Standard Bearer","Strategist","Wave Rider"]
#*
,
'druid': ['base','Animal Lord', 'Aquatic Druid', 'Arboreal Druid', 'Blight Druid', 'Blistering Invective Druid', 'Cave Druid', 'Chaos Beast', 'Cleric of the Cudgel', 'Demoniac', 'Dragon Herald', 'Dread Druid', 'Druid of Decay', 'Druid of the Swarm', 'Elemental Ally', 'Elemental Druid', 'Elemental Scion', 'Feyspeaker', 'Green Faith Acolyte', 'Hedge Witch', 'Herald Caller', 'Hinterlander', 'Infiltrator', 'Ley Line Guardian', 'Lion Shaman', 'Menhir Savant', 'Mooncaller', 'Nature Fang', 'Nature Warden', 'Pack Lord', 'Primal Companion Hunter', 'Rage Prophet', 'Ranger', 'Ravager', 'Reincarnated Druid', 'Saurian Shaman', 'Serpentfire Adept', 'Shaman', 'Shapeshifter', 'Storm Druid', 'Storval Stalker', 'Street Performer', 'Totemic Druid', 'Twilight Sage', 'Urban Druid', 'Verdant Druid', 'Visionary Seeker', 'Vulture Shaman', 'White-Haired Witch', 'Wild Whisperer']
,
#
'fighter': ['base','Tribal Defender', 'Biathlete', 'Road Warrior', 'Aether Soldier', 'Warmachine', 'Harrier', 'Knife Fighter', 'Man-at-Arms', 'Berserker', 'Chain Lasher', 'Challenger', 'Bonded Pet', 'Blade Shifter', 'Technique Master', 'Ironborn', 'Myrmidon', 'Silverblade Hunter', 'Swordsmith', 'Chakram Dervish', 'Quickblade', 'Spellscorn Fighter', 'Coachman', 'Tjuman', 'Pugilist', 'Ructioneer', 'Warrior of the Path', 'Scrapper', 'Aerial Assaulter', 'Spear Fighter', 'Skirmisher', 'Tribal Fighter', 'Venomblade', 'Viking', 'Aquanaut', 'Armiger', 'Defender', 'Lore Warden', 'High Guardian', 'Opportunist Fighter', 'Cyber-Soldier', 'Unbreakable', 'Phalanx Soldier', 'Gladiator', 'Gloomblade', 'Archer', 'Armor Master', 'Blackjack', 'Border Defender', 'Brawler', 'Buckler Duelist', 'Cad', 'Child of War', 'Corsair', 'Crossbowman', 'Dervish of Dawn', 'Dragonheir Scion', 'Dragoon', 'Drill Sergeant', 'Eldritch Guardian', 'Free Hand Fighter', 'Free-Style Fighter', 'Learned Duelist', 'Titan Fighter', 'Seasoned Commander', 'Martial Master', 'Mobile Fighter', 'Mutation Warrior', 'Pack Mule', 'Polearm Master', 'Relic Master', 'Roughrider', 'Savage Warrior', 'Sensate', 'Shielded Fighter', 'Siegebreaker', 'Steelbound Fighter', 'Swordlord', 'Tactician', 'Thunderstriker', 'Tower Shield Specialist', 'Trench Fighter', 'Two-Handed Fighter', 'Two-Weapon Warrior', 'Unarmed Fighter', 'Vengeful Hunter', 'Viking', 'Weapon Bearer Squire', 'Weapon Master', 'Warshade', 'Kappa-Bushi', 'Peltast', 'Tengubushi', 'Yakuza Bushi', 'Dragon Warrior']
,
#
'gunslinger': ['base','Bolt Ace', 'Breaker', 'Bushwacker', 'Chronicler', 'Desperado', 'Dragoon', 'Firebrand', 'Grenadier', 'Gun Scavenger', 'Gun Tank', 'Mysterious Stranger', 'Musket Master', 'Nimble Shot', 'Pistolero', 'Pistolero Exemplar', 'Pirate', 'Rocketslinger', 'Sniper', 'Thunderstriker', 'Vigilante']
#
,
'hunter': ['base',"Chameleon Adept","Colluding Scoundrel","Feykiller","Flood Flourisher","Forester","Plant Master","Treestrider","Aquatic Beastmaster","Pelagic Hunter","Totem-Bonded","Blight Scout","Courtly Hunter","Divine Hunter","Feral Hunter","Packmaster","Patient Ambusher","Primal Companion","Roof Runner","Scarab Stalker","Urban Hunter"]
#
,
'investigator': ['base',"Demolitionist","Engineer (Investigator Archetype)","Antiquarian","Jinyiwei","Tekritanin Arbiter","Portal Seeker","Cartographer","Malice Binder","Natural Philosopher","Reckless Epicurean","Ruthless Agent","Star Watcher","Toxin Codexer","Scavenger Investigator","Forensic Physician","Relentless Inspector","Guardian of Immortality","Profiler","Bonded Investigator","Cipher","Conspirator","Cryptid Scholar","Cult Hunter","Dread Investigator","Empiricist","Gravedigger","Hallucinist","Infiltrator","Lamplighter","Majordomo","Mastermind","Psychic Detective","Questioner","Skeptic","Sleuth","Spiritualist"]
#
,
'inquisitor': ['base','Conversion Inquisitor', 'Daemon Slayer', 'Ecclesitheurge', 'Exorcist', 'Forensic Physician', 'Heretic', 'Infiltrator', 'Inheritors Crusader', 'Judgmental Crusader', 'Monster Tactician', 'Preacher', 'Prepared Inquisitor', 'Sacred Huntmaster', 'Sanctified Prophet', 'Sin Seeker', 'Spellbreaker', 'Witch Hunter', 'Agent of the Grave', 'Divine Assessor', 'Enlightened Paladin', 'Living Grimoire', 'Tactical Leader', 'Umbral Agent', 'Spellkiller', 'Threatener']#
#
,
'unchained monk': ['base','Black Asp', 'Chained Monk', 'Drunken Master', 'Flowing Monk', 'Gong-Fu Disciple', 'Hamatula Strike Monk', 'Hungry Ghost Monk', 'Iron Mountain', 'Ki Mystic', 'Ki Warrior', 'Lotus Geisha', 'Martial Artist', 'Master of Many Styles', 'Monk of the Four Winds', 'Monk of the Healing Hand', 'Monk of the Iron Mountain', 'Monk of the Lotus', 'Monk of the Mantis', 'Monk of the Sacred Mountain', 'Monk of the Seven Winds', 'Monk of the Silver Fist', 'Monk of the Third Eye', 'Mute Monk', 'Nagaji Sensei', 'Nornkith', 'Ouat Monk', 'Sacred Fist', 'Scaled Fist', 'Sensei', 'Sohei', 'Soothsayer', 'Soulknife Monk', 'Swordmaster', 'Tattooed Monk', 'Teisatsu', 'Thunderstriker', 'Unchained Monk', 'Weapon Adept']
#
,
'magus': ['base',"Bladebound", "Eldritch Archer", "Hexcrafter", "Kensai", "Myrmidarch", "Staff Magus"]
#
,
'medium': ['base',"Angelic Aspect","Elemental Acuity","Fey Foundling","Fiend Keeper","Guardian","Haunted","Harrowed","Karmic Monk","Legendary Influence","Ley Line Guardian","Mind Reader","Possessed Hand","Relic Channeler","Scourge","Séance Channeler","Speaker for the Past","Storyteller","Twinned Summoner","Vessel of the Spirit"]
#
,
'mesmerist': ['base',"Cerulean Witch","Cult Leader","Enigma","Esotericist","Ethersinger","Eyebiter","Hypnotist","Lurker in Light","Mage of the Veil","Mindfreak","Seducer","Spirit Walker","Starwatcher","Thrallherd","Umbral Mesmerist","Vexing Daredevil","White Mage"]
#
,
'ninja': ['base',"Shadow Walker", "Master of Many Styles", "Tengu Assassin", "Shadow Scion", "Poison Master", "Harvester of Sorrows", "Ninpo Maniac", "Flurry of Stars", "Sanguine Angel", "Blighted Myrmidon", "Zen Archer", "Shikigami Style", "Scarred Monk", "Snakebite Striker", "Vanishing Assassin"]
#
,
'occultist':['base',"Battle Host", "Panoply Savant", "Reliquarian", "Silksworn", "Souldrinker", "Transmuter"]
#*
,

'oracle': ['base',"Dual-Cursed Oracle","Elemental Oracle","Heavens Oracle","Lunar Oracle","Nature Oracle","Life Oracle","Ancestor Oracle","Battle Oracle","Bones Oracle","Dark Tapestry Oracle","Deep Earth Oracle","Dragon Oracle","Flame Oracle","Metal Oracle","Outer Rifts Oracle","Waves Oracle","Wind Oracle","Time Oracle","Solar Oracle","Lunar Paragon","Cosmic Champion (Oracle)","Devoted Oracle (Oracle)","Entranced Warrior (Champion Oracle)","Pale Rider (Duskwalker Oracle)","Pantheist Oracle (Oracle)","Revelator (Oracle)","Runist (Oracle)","Sortilega (Oracle)","Spiritist (Oracle)","Divine Numerologist","Elementalist Oracle","Hermit","River Soul","Tree Soul","Ocean's Echo","Divine Herbalist","Possessed Oracle","Inerrant Voice","Prophet","Black-Blooded Oracle","Cyclopean Seer","Dual-Cursed Oracle","Elementalist Oracle (PotS)","Enlightened Philosopher","Planar Oracle","Psychic Searcher","Seeker","Seer","Spirit Guide","Stargazer","Warsighted"]
#*
,
'paladin' : ['base',"Divine Calling","Shadow Banisher","Knight Disciple","Dashing Hero","Horned Warden","Righteous Flame Acolyte","Spirit-Scarred Paladin","Knight of the Road","Village Champion","Consecrator (Paladin Archetype)","Fate Swayer (Paladin Archetype)","Spear Maiden","Coastal Defender","Sacred Flame","Chevalier","Dragon Knight","Champion of the Cascade","Forgefather Seeker","Chaos Knight","Knight of Coins","Banishing Warden","Faithful Wanderer","Forest Preserver","Hunting Paladin","Vindictive Bastard","Wilderness Warden","Kraken Slayer","Pearl Seeker","Scion of Peace","Chosen One","Combat Healer Squire","Divine Defender","Divine Guardian","Divine Hunter","Dusk Knight","Empyreal Knight","Enforcer","Enlightened Paladin","Ghost Hunter","Gray Paladin","Holy Guide","Holy Gun","Holy Tactician","Hospitaler","Legate","Martyr","Mind Sword","Oathbound Paladin","Sacred Servant","Sacred Shield","Shining Knight","Silver Champion","Soul Sentinel","Sword of Valor","Tempered Champion","Temple Champion","Tortured Crusader","Undead Scourge","Virtuous Bravo","Warrior of the Holy Light"]
,
#*
'psychic': ["Amnesiac","Esoteric Starseeker (Psychic Archetype)","Formless Adept","Mutation Mind","Psychic Duelist","Psychic Marauder","Terror Weaver","Wildepath (Psychic Archetype)"]
#*
,
'rogue':  ['base',"SpellResistance", "ScourgeofShadows", "HiddenBlade", "Menteur(Elan)", "ReavingRaider(Maenad)", "Chemist", "DungeonRunner", "Fence", "GloryRogue", "ImperialFlanker", "Mageslayer", "Medic", "PetTrainer", "Stalker", "StreetMagician", "StreetUrchin", "TrueProfessional", "UrbanNinja", "WeaponExpert", "Bomber", "Hitman", "Nightmage", "BankRobber", "CultDefector", "Rustler", "GreaseRat", "Poacher", "Snowbird", "ConstructSaboteur", "Dreamthief", "NamelessShadow", "DesertRaider", "DiscretionSpecialist", "FeyPrankster", "GunSmuggler", "Needler", "Rotdrinker", "ShadowScion", "SlySaboteur", "SwampPoisoner(Grippli)", "SylvanTrickster", "Earthshadow", "Irrigator", "SeekeroftheLost", "TidalTrickster", "ToxicTalon", "Acrobat", "Agitator", "Bandit", "Burglar", "Carnivalist", "Chameleon", "Charlatan", "Consigliere", "CounterfeitMage", "Cutpurse", "DarkLurker", "Driver", "EldritchScoundrel", "Escapologist", "FalseMedium", "Guerrilla", "GuildAgent", "Heister", "Investigator", "Kidnapper", "KnifeMaster", "Liberator", "MakeshiftScrapper", "MasterofDisguise", "PhantomThief", "Pirate", "PlanarSneak", "Poisoner", "Rake", "RelicRaider", "RiverRat", "RoofRunner", "SanctifiedRogue", "Sapper", "Scavenger", "Scout", "ScrollScoundrel", "ShadowRebel", "ShadowWalker", "Sharper", "Smuggler", "Sniper", "Snoop", "Spy", "Survivalist", "Swashbuckler", "Swindler"]
,
#*
'ranger':  ['base',"Heart of the Forest","Ambush Hunter","Kinslayer (Half-Giant)","Cloaked Killer","Divinely Bound Ranger","Grasslands Prowler","Commando","Yuam","Blockade Runner","Bombardier (Ranger Archetype)","Robot Fighter (Ranger Archetype)","Creationist","Musher","Dragon Hunter","Blood Hunter (Ranger Archetype)","Lycanthrope Hunter","Planar Scout","Blightwarden","Deeplands Sailor","Elemental Envoy","Flamewarden","Stormwalker","Summit Sentinel","Tidal Hunter","Toxic Herbalist","Wild Soul","Wilderness Explorer","Deep Diver","Lantern Lighter","Raven Master","Poison Darter","Wilderness Medic","Lantern Bearer","Fortune Finder","Infiltrator","Battle Scout","Beastmaster","Bow Nomad (Kasatha)","Cinderwalker","Code Runner","Corpse Hunter","Dandy","Deep Walker","Demonslayer","Divine Marksman","Divine Tracker","Dragon Hunter","Drake Warden","Dungeon Rover","Falconer","Freebooter","Galvanic Saboteur","Groom","Guide","Guildbreaker","Hooded Champion","Horse Lord","Sentinel","Shapeshifter","Skirmisher","Sky Stalker","Spirit Ranger","Toxophilite","Transporter","Trapper","Trophy Hunter","Urban Ranger","Warden","Wild Hunter","Wild Stalker","Witchguard","Woodland Skirmisher","Yokai Hunter","Seabeast Hunter (Gnorri)","Foe Reaper","Henge Matagi","Pack Hunter","Yojimbo","Golem Slayer","Pack-Bonded Hunter (Gnoll)","Wolf Heart","Wolf Heart","Arcanger","Churimanger","Unearthed Ranger"]
,
#*
'sorcerer': ['base',"Learned Sorcery","Nine-Tailed Mystic (Kitsune)","Sanctified Sorcerer","Nanotech Infuser","Mongrel Mage","Crossblooded","Dragon Drinker","Eldritch Scrapper","False Priest","Seeker","Sorcerer of Sleep","Stone Warder","Tattooed Sorcerer","Umbral Scion","Wildblooded","Familiar","Magilith","Arcane Endowments","Bedreven","Bloodless","Scourge","Strega"]
#*
,
'spiritualist': ["Ectoplasmatist","Exciter","Fated Guide","Fractured Mind","Geist Channeler","Grim Apostle","Hag-Haunted","Haunted","Involutionist","Necrologist","Onmyoji","Phantom Blade","Plague Eater","Priest of the Fallen","Scourge","Seeker of Enlightenment","Shadow Caller","Soul Warden","Spirit Fuse","Totem Spiritualist","Usher of Lost Souls","Ward Spiritualist","Zeitgeist Binder"]
#*
,
'shifter': ['base',"Dragonblood Shifter","Feyform Shifter","Holy Beast","Swarm Shifter","Style Shifter","Wild Effigy","Adaptive Shifter","Elementalist Shifter","Fiendflesh Shifter","Leafshifter","Oozemorph","Rageshaper","Verdant Shifter","Weretouched"]
#*
,
'summoner': ['base',"Blood God Disciple","Broodmaster","Clan Summoner","Creative Artist","Demon Binder","Divine Summoner","Evolutionist","First Worlder","God Caller","Hostile Summoner","Leshy Caller","Master Summoner","Monster Ally","Monster Channeler","Monster Knight","Monster Magus","Morphic Savant","Muse-Touched (Summoner Archetype)","Naturalist","Pyroclast","Spirit Summoner","Spellbook Summoner","Story Summoner","Storm Caller","Synthesist","Twinned Summoner","Unwavering Conduit","Wild Caller","Celestial Commander","Progenitor"]
#*
,

'shaman': ['base',"Darkness","Metal","Aether","AkashicRecords","ShamanOfTheElements","Jiuweihu","CrystalTender","GraspingVine","PrimalWarden","DeepShaman","Name-Keeper","SerendipityShaman","DraconicShaman","Animist","Overseer","PossessedShaman","SpeakerForThePast","SpiritWarden","TrueSilveredThrone","UnswornShaman","Visionary","WitchDoctor","Bloodlust","FeralSpirit","FuryOfTheWind","GhostWolf","Maelstrom","PersonalReincarnation","Stormbringer","WaterWalking","Frost","Tribe","Ancestors","Battle","Bones","Flame","Heavens","Life","Lore","Mammoth","Nature","Slums","Stone","Waves","Wind","Wood"]
#*
,
'swashbuckler': ['base',"corsair","daringinfiltrator","flyingblade","inspiredblade","guidingblade","mouser","musketeer","mysteriousavenger","picaroon","whirlingdervish","ronin"]
#*
,
'warpriest': ['base',"Arsenal Chaplain""Champion of The Faith""Cult Leader""Disenchanter""Divine Commander""Feral Champion""Forgepriest""Liberty’s Blade""Mantis Zealot""Proselytizer""Sacred Fist""Shieldbearer""Faithful Paragon""Soldier of Gaia"]
#*
,
'warlock': ['base']
#*
,
'witch': ['base',"Jewel Bound Familiar","Skullbound Shapechanger","Ancestral Disapproval","Ancestral Hex","Ancestral Knowledge","Bat Sneeze","Become Familiar","Borrow Speed","Dire Familiar","Drain Life","Fear of Death","Leg Lock","Steal Life","Swift Step","Aura of Purity","Beast of Ill-Omen","Blight","Cackle","Cauldron","Charm","Child-Scent","Coven","Cursed Wound","Discord","Disguise","Disrupt Connection","Evil Eye","Feral Speech","Flight","Fortune","Healing","Misfortune","Mud Witch","Nails","Peacebond","Poison Steep","Prehensile Hair","Scar","Slumber","Soothsayer","Swamp Hag","Swamp's Grasp","Tongues","Unnerve Beasts","Ward","Water Lung","Witch's Bottle","Agony","Beast Eye","Animal Skin","Cook People","Delicious Fright","Hag's Eye","Harrowing Curse","Hidden Home","Hoarfrost","Ice Tomb","Infected Wounds","Major Healing","Nightmares","Pariah","Retribution","Speak in Dreams","Steal Voice","Vision","Waxen Image","Weather Control","Witch's Bounty","Witch's Charge","Witch's Brew","Abominate","Curse of Nor","Death Curse","Dire Prophecy","Eternal Slumber","Forced Reincarnation","Lay to Rest","Life Giver","Natural Disaster","Summon Spirit","Witch's Hut"]
#*
,
'wizard': ['base',"Cryomancer Wizard", "Fundamentalist Wizard", "Pine Baron", "Delver", "Animist", "Astromancer", "Blood Mage", "Chaos Mage", "Clockworker", "Geomancer", "Iounmancer", "Ring Warden (Dwarf)", "Timekeeper", "Vril Adept", "Petersen Games - Wizard", "Ritualist", "Ruin Guardian (Zoog)", "d20pfsrd.com Publishing - Wizard", "Circulumancer", "Echo Bonded", "4 Winds Fantasy Gaming - Wizard", "Intuitive Wizardry", "Gold-Robed Wizard",  "Bestial Arcanist", "Ilumbo",  "Sutramancer", "Paizo, Inc. - Wizard", "Clocksmith", "Arcane Warden", "Poleiheira Adherent", "Fey Caller", "Worldseeker", "Chronomancer", "Runesage", "Arcane Bomber", "Arcane Physician", "Bonded Wizard", "Elder Mythos Scholar", "Exploiter Wizard", "Familiar Adept", "Hallowed Necromancer", "Instructor", "Pact Wizard (FF)", "Pact Wizard (HH)", "Primalist", "Scroll Scholar", "Scrollmaster", "Shadowcaster", "Siege Mage", "Spell Sage", "Spellslinger", "Spirit Binder", "Spirit Whisperer", "Sword Binder", "Undead Master", "Radiance House - Wizard", "Soul Weaver", "Dweomerden Wizard", "Force Commander", "Glamerforge Wizard", "Horimyo", "Nethervault Wizard", "Onmyoji"]
#*
,
#Path of War Archetypes:

'harbringer': ['base','Crimson Countess','Omen Rider','Ravenlord']
,
#
'mystic': ['base','Aurora Soul','Gunsmoke Mystic','Knight-Chandler']
,
#
"Stalker": ['base',"Brutal Slayer","Judge","Soul Hunter","Vigilante"]
#
,
'warder': ['base','Dervish Defender','Fiendbound Marauder','Hawkguard','Ordained Defender','Sworn Protector','Zweihander Sentinel']
#
,
"Warlord": ['base',"Bannerman","Desperado","Steelfist Commando","Vanguard Commander"]
#
,
"Zealot": ['base',"Discordant Crusader","Void Prophet"]
,
# Spheres of might Archetypes:
'armiger': ['base',"Antiquarian", "Awakener", "Battlefield Tinker", "Bladewalker", "Bounty Hunter", "Machinehead", "Stancemaster"]
#
,
'blacksmith': ['base','Barista [Apoc]', 'Disciple of Goibniu', 'Essence Smith [Apoc, CS]', 'Fleshforger', 'Iron Chef', 'Master-At-Arms [3PP]', 'Spellforge [CS]', 'Techsmith']
#
,
'commander':['base',"Bearon [CS]", "Braveheart", "Dreadlord [CS]", "Feylord [CS]", "Noble", "Vanguard", "Visionary General [CS]"]
#
,
'conscript':['base',"Alchemy","Athletics","Barrage","Barroom","Beastmastery","Berserker","Boxing","Brute","Dual Wielding","Duelist","Equipment","Fencing","Gladiator","Guardian","Lancer","Open Hand","Scoundrel","Scout","Shield","Sniper","Trap","Warleader","Wrestling"]
#
,
'savant': ['base']
#
,
'scholar': ['base',"Astrologian [CS]", "Caller [CS]", "Doctor", "Fell Archaeologist", "Harmacist", "Slime Savant", "Stitcher [CS]"]
#
,
'sentinel': ['base',"Barfighter", "Black Powder Brawler", "Chaos Shifter", "Elemental Fist [CS]", "Shadowed Fist", "Skirmishing Scout", "Strong Style Grappler"]
#
,
'striker': ['base',"Barfighter", "Black Powder Brawler", "Chaos Shifter", "Elemental Fist [CS]", "Shadowed Fist", "Skirmishing Scout", "Strong Style Grappler"]
#
,
'technician': ['base',"Adamantine Scientist", "Mad Scientist", "Mythbreaker", "Rigger", "Suit Pilots"]
#
,
#Spheres of power Archetypes:
'armorist': [ 'base',   "Blaster",    "Bloodbinder [CS]",    "Bonewright",    "Collector",    "Darkshaper",    "Ferrous Emissary",    "Inventioneer [CS]",    "Lingchi Warrior",    "Living Weapon",    "Martial Armorist [CS]",    "Soaring Blade",    "Spirit Blade [CS]",    "Symbiotic Knight",    "Vajrahasta [CS]",    "Void Wielder",    "Warden",    "Warleader",    "Whitesmith"]
#
,
'elementalist':['base',"Admixture Savant", "Arcanophage", "Arcanopulser", "Earth Warrior", "Electrokinetic", "Elemontalist", "Flame Warrior", "Geomancer", "Martial Elementalist", "Metal Warrior", "Natural Warrior", "Soul Adept", "Tenebrous Stalker", "Twinsoul Elementalist", "Water Warrior", "Wind Warrior"]
#
,
'eliciter': ['base',"Dark Presence","Empathic Duelist","Fright Wright","Hypnotist","Id","Sympath"]
#
,
'fey adept': ['base',"dreamtwister","seelie disciple","sidhe invoker","skulk","solipsist","unseelie disciple","word witch","wunderkind"]
#
,
'hedgewitch':['base',"Dreamtwister","Seelie Disciple","Sidhe Invoker","Skulk","Solipsist","Unseelie Disciple","Word Witch","Wunderkind [WoP]"]
#
,
'incanter': ["Alteration","Blood","Conjuration","Creation","Dark","Death","Destruction","Divination","Enhancement","Fallen Fey","Fate","Illusion","Life","Light","Mana","Mind","Nature","Protection","Telekinesis","Time","War","Warp","Weather"]
#
,
'mageknight': ['base',"Broadcast Blade","Divine Lariat","Doomblade","Dragoon","Dread Crusader","Dustbringer","Grim Disciple","Herculean Scion","Kinetic Scourge","Knightknight","Knight-Summoner","Marshal Controller [CS]","Martial Mageknight [CS]","Plaguebringer","Resizer","Sun Warrior","Utterdark Champion","Wardmage","Warrior of Holy Light"]
#
,
'shifter': ['base',"ApexShifter","Beastlord","Beastmind","DimensionShifter","ElementalScion","FamineSpirit","FeyIncarnate","ForcefulShifter","MartialShifter[CS]","NocturnalPredator","PackMaster","Paragon[CS]","Protean","RadiantProtean","Spellvampire"]
#
,
'soul weaver':['base',"Banshee", "CycleWatcher", "DualChanneler", "GhostSovereign", "Lichling", "Pharmakon", "Shaman[WoP]", "ShepherdoftheLost", "Totemist"]
#
,
'symbiat': ['base',"Battlemind[CS]","Bloodscarred","Champion Symbiat[CS]","Chronomancer","Egregore","Gravecrawler","Hekatonkheires","Invidian","Malefactor","Mistwalker","Operative","Synapse","Technopath[3PP]","Telekinetic Warrior","Vector[CS]","Warmonger"]
#
,
'thamaturge': ['base',"Banshee", "CycleWatcher", "DualChanneler", "GhostSovereign", "Lichling", "Pharmakon", "Shaman [WoP]", "ShepherdOfTheLost", "Totemist", "Battlemind [CS]", "Bloodscarred", "ChampionSymbiat [CS]", "Chronomancer", "Egregore", "Gravecrawler", "Hekatonkheires", "Invidian", "Malefactor", "Mistwalker", "Operative", "Synapse", "Technopath [3PP]", "TelekineticWarrior", "Vector [CS]", "Warmonger", "Devourer", "EldritchCultist", "Experimentalist", "Gambler [CS/3PP]", "KnightOfWillpower", "MartialThaumaturge [CS]", "PactMaster", "Pactmage", "Savant", "SoulfireMaster", "UnseenHorror", "VoidGazer", "WildMage"]
#
,
'wraith': ['base',"BaobhanSith","Collective[CS]","Draugr[CS]","Matagot[CS,CatgirlHB]","Mistshade","Swarmheart","Unbodied"]
#
,
#spheres of power champions
'crimson dancer': ['base',"Crimson Tempest", "Path of the Lost Ravager", "Primeval"]
#
,
'dragoon': ['base','Mech Dragoon', 'Spellscale', 'violent Brute']
#
,
'mountebank': ['base','back alley grifter', 'Mental Manipulator', 'Phantom thief']
#
,
'necros': ["Brutal Necromancer", "Necrotech Savant"]
#
,
'prodigy': ['base','battle-born','chromamancer','extemporizer','gutter rat', 'mimic']
#
,
'reaper': ['base','chem dog', 'Discipline of the monstrous arts', 'hunt master', 'machine cultist', 'magekiller']
#
,
'sage': ['base','Battleshifter', 'Confluence', 'Resolute', 'Votary', 'Wand Master']
#
,
'troubadour': ['base',"binder","clone","method actor","ringmaster"]
#
,
'warden': ['base','Custodian', 'Empathetic Guardian', 'Jailer', 'Keeper']
#
,
#spheres of power agents
'agent': ['base','Blackpowder Slayer', 'Erudie Pugilist', 'Imposter', 'Superstar Spy']
#
,
'courser': ['base',"Gourmand", "Nomad", "Ravener"]
#
,
'envoy': ['base',"Aristarch", "Idol", "Luminary"]
#
,
'mastermind': ['base','Saboteur', 'Squad Operator']
#
,
'professional': ['base','Trader']
}

                    #Path of war classes

version = "4/30/23"
