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
'fighter': ['base','Tribal Defender', 'Biathlete', 'Road Warrior', 'Aether Soldier', 'Warmachine', 'Harrier', 'Knife Fighter', 'Man-at-Arms', 'Berserker', 'Chain Lasher', 'Challenger', 'Bonded Pet', 'Blade Shifter', 'Technique Master', 'Ironborn', 'Myrmidon', 'Silverblade Hunter', 'Swordsmith', 'Chakram Dervish', 'Quickblade', 'Spellscorn Fighter', 'Coachman', 'Tjuman', 'Pugilist', 'Ructioneer', 'Warrior of the Path', 'Scrapper', 'Aerial Assaulter', 'Spear Fighter', 'Skirmisher', 'Tribal Fighter', 'Venomblade', 'Viking', 'Aquanaut', 'Armiger', 'Defender', 'Lore Warden', 'High Guardian', 'Opportunist Fighter', 'Cyber-Soldier', 'Unbreakable', 'Phalanx Soldier', 'Gladiator', 'Gloomblade', 'Archer', 'Armor Master', 'Blackjack', 'Border Defender', 'Brawler', 'Buckler Duelist', 'Cad', 'Child of War', 'Corsair', 'Crossbowman', 'Dervish of Dawn', 'Dragonheir Scion', 'Dragoon', 'Drill Sergeant', 'Eldritch Guardian', 'Free Hand Fighter', 'Free-Style Fighter', 'Learned Duelist', 'Titan Fighter', 'Seasoned Commander', 'Martial Master', 'Mobile Fighter', 'Mutation Warrior', 'Pack Mule', 'Polearm Master', 'Relic Master', 'Roughrider', 'Savage Warrior', 'Sensate', 'Shielded Fighter', 'Siegebreaker', 'Steelbound Fighter', 'Swordlord', 'Tactician', 'Thunderstriker', 'Tower Shield Specialist', 'Trench Fighter', 'Two-Handed Fighter', 'Two-Weapon Warrior', 'Unarmed Fighter', 'Vengeful Hunter', 'Viking', 'Weapon Bearer Squire', 'Weapon Master', 'Warshade', 'Kappa-Bushi', 'Peltast', 'Tengubushi', 'Yakuza Bushi', 'Dragon Warrior']
,
#
'barbarian': ['base','Armored Hulk','Beastkin Berserker','Blooded Arcanist','Breaker','Brutal Pugilist','Cannibal','Chaos Totem','Dreadnought','Elemental Kin','Fated Champion','Feral Gnasher','Flesheater','Furyborn','Goliath Druid','Hateful Rager','Hurler','Invulnerable Rager','Lion Blade','Marauder','Mooncursed','Mounted Fury','Pack Rager','Primal Hunter','Primalist','Raging Cannibal','Raging Cyclone','Raging Drunk','Raging Flame','Raging Hurler','Raging Tactician','Savage Barbarian','Scarred Rager','Sea Reaver','Shaman','Skeletal Champion','Spell Sunderer','Steel-Breaker','Superstitious','Survivor','Titan Mauler','Totem Warrior','True Primitive','Unchained Rager','Urban Barbarian','Wild Rager']
,
#
'druid': ['base','Animal Lord', 'Aquatic Druid', 'Arboreal Druid', 'Blight Druid', 'Blistering Invective Druid', 'Cave Druid', 'Chaos Beast', 'Cleric of the Cudgel', 'Demoniac', 'Dragon Herald', 'Dread Druid', 'Druid of Decay', 'Druid of the Swarm', 'Elemental Ally', 'Elemental Druid', 'Elemental Scion', 'Feyspeaker', 'Green Faith Acolyte', 'Hedge Witch', 'Herald Caller', 'Hinterlander', 'Infiltrator', 'Ley Line Guardian', 'Lion Shaman', 'Menhir Savant', 'Mooncaller', 'Nature Fang', 'Nature Warden', 'Pack Lord', 'Primal Companion Hunter', 'Rage Prophet', 'Ranger', 'Ravager', 'Reincarnated Druid', 'Saurian Shaman', 'Serpentfire Adept', 'Shaman', 'Shapeshifter', 'Storm Druid', 'Storval Stalker', 'Street Performer', 'Totemic Druid', 'Twilight Sage', 'Urban Druid', 'Verdant Druid', 'Visionary Seeker', 'Vulture Shaman', 'White-Haired Witch', 'Wild Whisperer']
,
#
'cleric': ['base','Angelfire Apostle', 'Anger Inquisition', 'Aquatic Druid', 'Arcanist', 'Atheist', 'Battle Priest', 'Chaos Channeler', 'Cloistered Cleric', 'Crusader', 'Divine Strategist', 'Evangelist', 'Exalted', 'Feral Hunter', 'Inheritors Crusader', 'Liturgical Mage', 'Merciful Healer', 'Necromancer', 'Planar Oracle', 'Ravener Hunter', 'Sanguine Angel', 'Separatist', 'Shaman', 'Theologian', 'Undead Lord', 'Varisian Pilgrim', 'Visionary Prophet']
,
#
'rogue':  ['base','Acrobat', 'Bandit', 'Beastmaster', 'Beguiler', 'Burglar', 'Charlatan', 'Chirurgeon', 'Circus Performer', 'Cloaked Dancer', 'Cloistered Cleric', 'Commando', 'Con Artist', 'Counterfeit Mage', 'Court Fool', 'Cutpurse', 'Daggermark Poisoner', 'Dandy', 'Dark Delver', 'Deep Walker', 'Demagogue', 'Dervish of Dawn', 'Eldritch Scoundrel', 'False Medium', 'Fast Hands', 'Gang Leader', 'Gloomblade', 'Guerrilla', 'Guild Agent', 'Guild Poisoner', 'Hidden Priest', 'Highwayman', 'Hooded Champion', 'Infiltrator', 'Knife Master', 'Liberator', 'Master Spy', 'Mouser', 'Natural Alchemist', 'Noble Fencer', 'Phantom Thief', 'Pilferer', 'Pirate', 'Poisoner', 'Rake', 'Rapscallion', 'Ratcatcher', 'Ringleader', 'Saboteur', 'Sandman', 'Sapper', 'Savage Skirmisher', 'Scavenger', 'Scout', 'Shadowdancer', 'Shadow Rager', 'Sleuth', 'Sniper', 'Spy', 'Stalker', 'Streetfighter', 'Survivalist', 'Swordmaster', 'Thief Acrobat', 'Thug', 'Trapsmith', 'Underground Chemist', 'Vexing Dodger', 'Vigilante', 'Wasp', 'Watersinger', 'Wild Child', 'Zealot']
,
#
'ranger':  ['base','Airborne Ambusher', 'Arboreal Ranger', 'Battle Scout', 'Beastmaster', 'Blightwarden', 'Bow Nomad', 'Cavalier', 'Child of Acavna and Amaznen', 'Deep Walker', 'Divine Marksman', 'Dragon Hunter', 'Duskwarden', 'Falconer', 'Favored Enemy (aquatic)', 'Favored Enemy (dungeon)', 'Favored Enemy (forest)', 'Favored Enemy (giant)', 'Favored Enemy (magical beast)', 'Favored Enemy (plant)', 'Favored Enemy (undead)', 'Frost Tusk', 'Geomancer', 'Ghost Hunter', 'Giant Killer', 'Guide', 'Harrow Warden', 'Hooded Champion', 'Horse Lord', 'Horizon Walker', 'Infiltrator', 'Initiate of the Hunt', 'Liberator', 'Lion Blade', 'Living Monolith', 'Master of Many Forms', 'Natural Warrior', 'Nature Warden', 'Pack Lord', 'Pathfinder Chronicler', 'Polearm Master', 'Reaper of Secrets', 'Sable Company Marine', 'Savage Skirmisher', 'Sea Dog', 'Skirmisher', 'Stormwalker', 'Strider', 'Swift Hunter', 'Terramancer', 'Thundercaller', 'Trapper', 'Treantmonk (Druid/Ranger)', 'Trick Shot', 'Trickster', 'Two-Handed Fighter', 'Urban Ranger', 'Verdant Sorcerer', 'Wild Shadow', 'Wild Stalker', 'Witch Hunter', 'Woodland Skirmisher', 'World Walker']
,
#
'paladin' : ['base','Angelfire Apostle', 'Blaze of Glory', 'Champion of the Faith', 'Chosen One', 'Divine Defender', 'Divine Hunter', 'Divine Strategist', 'Divine Warrior', 'Divine Weapon', 'Eagle Knight', 'Empyreal Knight', 'Enlightened Paladin', 'Erastils Boon', 'Holy Gun', 'Holy Tactician', 'Hospitaler', 'Inheritors Crusader', 'Knight of Ozem', 'Knight of the Sepulcher', 'Lion Blade', 'Living Grimoire', 'Oathbound Paladin', 'Oath of Charity', 'Oath of Chivalry', 'Oath of Duty', 'Oath of Loyalty', 'Oath of the Crown', 'Oath of the People', 'Oath of Vengeance', 'Oath against Savagery', 'Oath of Empathy', 'Oath of the Open Hand', 'Sacred Servant', 'Sanctified Prophet', 'Shining Knight', 'Undead Scourge']
,
#
'alchemist': ['base','Alchemical Trapper', 'Apothecary', 'Beastmorph', 'Blood Alchemist', 'Bombardier', 'Chirurgeon', 'Clone Master', 'Construct Rider', 'Crypt Breaker', 'Ectoplasm Master', 'Elemental Master', 'Experimental Gunsmith', 'Feral Mutagen', 'Frost Rider', 'Grenadier', 'Gunslinger Alchemist', 'Infernal Alchemist', 'Inspired Chemist', 'Master Chymist', 'Mindchemist', 'Mutation Warrior', 'Plague Bringer', 'Psychonaut', 'Reanimator', 'Sapper', 'Soulforger', 'Spagyrist', 'Spelleater', 'Spirit Whisperer', 'Totemic Summoner', 'Twilight Sage', 'Vivisectionist']
#
,
'monk': ['base','Black Asp', 'Chained Monk', 'Drunken Master', 'Flowing Monk', 'Gong-Fu Disciple', 'Hamatula Strike Monk', 'Hungry Ghost Monk', 'Iron Mountain', 'Ki Mystic', 'Ki Warrior', 'Lotus Geisha', 'Martial Artist', 'Master of Many Styles', 'Monk of the Four Winds', 'Monk of the Healing Hand', 'Monk of the Iron Mountain', 'Monk of the Lotus', 'Monk of the Mantis', 'Monk of the Sacred Mountain', 'Monk of the Seven Winds', 'Monk of the Silver Fist', 'Monk of the Third Eye', 'Mute Monk', 'Nagaji Sensei', 'Nornkith', 'Ouat Monk', 'Sacred Fist', 'Scaled Fist', 'Sensei', 'Sohei', 'Soothsayer', 'Soulknife Monk', 'Swordmaster', 'Tattooed Monk', 'Teisatsu', 'Thunderstriker', 'Unchained Monk', 'Weapon Adept']
#
,
'magus': ['base',"Bladebound", "Eldritch Archer", "Hexcrafter", "Kensai", "Myrmidarch", "Staff Magus"]
#
,
'wizard': ['base','Arcane Bomber', 'Bladesinger', 'Chronomancer', 'Diviner', 'Elemental Master', 'Foresightful', 'Illusionist', 'Infernal Binder', 'Magical Child', 'Martial Mage', 'Necromancer', 'Occultist', 'Shadowcaster', 'Spell Sage', 'Summoner', 'Thassilonian Specialist', 'Scroll Scholar', 'Spellbinder', 'Spirit Binder', 'Spirit Whisperer', 'Spontaneous Mage', 'Teleportation Master', 'Thaumaturge', 'Universalist', 'Undead Master']
#
,
'sorceror': ['base','Abyssal Bloodline', 'Accursed', 'Ardent', 'Boreal', 'Brutal', 'Celestial Bloodline', 'Chaos', 'Crossblooded', 'Daemon', 'Djinni', 'Draconic Bloodline', 'Dreamspun', 'Efreeti', 'Elemental Bloodline', 'Empyreal Bloodline', 'Fey Bloodline', 'Ghoul', 'Harrowing', 'Imperious', 'Infernal Bloodline', 'Marid', 'Maestro', 'Psychic Bloodline', 'Rakshasa', 'Razmiran Priest', 'Sanguine', 'Serpentine', 'Shadow', 'Shaitan', 'Stormborn', 'Undead Bloodline', 'Verdant', 'Wildblooded']
#
,
'anti-paladin': ['base','Apostate', 'Atheist', 'Beast Lord', 'Blacker of the Blackest Black', 'Blackguard', 'Brutal Fiend', 'Chosen One', 'Conqueror', 'Cowled Rider', 'Crimson Templar', 'Cult Slayer', 'Deathtouched', 'Demagogue', 'Demoniac', 'Demonic Champion', 'Demonologist', 'Devil Eater', 'Devils Arm', 'Disciple of Whispers', 'Dread Vanguard', 'Drow Nobility', 'Duellist', 'Executioner', 'Fell Rider', 'Fiend Keeper', 'Fiendish Vessel', 'Glorifier', 'Green Faith Acolyte', 'Hell Knight', 'Hells Vengeance Commander', 'Herald of the Horned King', 'Horseman of the Apocalypse', 'Houndlord', 'Hungerseed', 'Hunter of the Dead', 'Insinuator', 'Knight of the Sepulcher', 'Knight of the Wastes', 'Knight of the Word', 'Martial Disciple', 'Master of Shrouds', 'Night Terror', 'Order of the Ebon Hand', 'Plaguebearer', 'Psychic Beacon', 'Reaper of Vengeance', 'Redeemer', 'Reliquarian', 'Ruin Delver', 'Sanguine Angel', 'Sanguine Disciple', 'Savage Barbarian', 'Seductive Whisperer', 'Senghorian Defender', 'Shadow Disciple', 'Skeletal Champion', 'Soul Flayer', 'Sword Scion', 'Terror Knight', 'Thrune Agent', 'Tyrant', 'Unbreakable Guardian', 'Undead Scourge', 'Unforgiving Zealot', 'Unholy Barrister', 'Unholy Vindicator', 'Warrior of the Holy Light', 'Whispering Wayfinder', 'Widowmaker']
#
,
'cavalier': ['base','Beast Rider', 'Bushi', 'Castellan', 'Chevalier', 'Constable', 'Daring Champion', 'Disciple of the Pike', 'Divine Commander', 'Emissary', 'Esquire', 'Fell Rider', 'Gendarme', 'Goblin Cleaver', 'Green Knight', 'Herald', 'Honor Guard', 'Huntmaster', 'Knight of the Wall', 'Luring Cavalier', 'Musketeer', 'Order of the Blossom', 'Order of the Cockatrice', 'Order of the Dragon', 'Order of the Eclipse', 'Order of the Flame', 'Order of the Lion', 'Order of the Penitent', 'Order of the Shield', 'Order of the Staff', 'Order of the Star', 'Order of the Sword', 'Order of the Tome', 'Order of the Wall', 'Pure Legionnaire', 'Quarterback', 'Samurai', 'Standard Bearer', 'Tactician', 'Thunderstriker', 'Vengeful Knight']
#
,
'gunslinger': ['base','Bolt Ace', 'Breaker', 'Bushwacker', 'Chronicler', 'Desperado', 'Dragoon', 'Firebrand', 'Grenadier', 'Gun Scavenger', 'Gun Tank', 'Mysterious Stranger', 'Musket Master', 'Nimble Shot', 'Pistolero', 'Pistolero Exemplar', 'Pirate', 'Rocketslinger', 'Sniper', 'Thunderstriker', 'Vigilante']
#
,
'inquisitor': ['base','Conversion Inquisitor', 'Daemon Slayer', 'Ecclesitheurge', 'Exorcist', 'Forensic Physician', 'Heretic', 'Infiltrator', 'Inheritors Crusader', 'Judgmental Crusader', 'Monster Tactician', 'Preacher', 'Prepared Inquisitor', 'Sacred Huntmaster', 'Sanctified Prophet', 'Sin Seeker', 'Spellbreaker', 'Witch Hunter', 'Agent of the Grave', 'Divine Assessor', 'Enlightened Paladin', 'Living Grimoire', 'Tactical Leader', 'Umbral Agent', 'Spellkiller', 'Threatener']#
,
'oracle': ['base','Ancient Lorekeeper', 'Black-Blooded Oracle', 'Blighted Myrmidon', 'Bones Oracle', 'Chosen One', 'Dark Tapestry', 'Dual-Cursed Oracle', 'Elemental Master', 'Enlightened Philosopher', 'Haunted', 'Heavens', 'Hedge Witch', 'Lunar', 'Nature Oracle', 'Noble Scion', 'Outer Rifts', 'Planar Oracle', 'Possessed', 'Seer', 'Shadow Oracle', 'Spirit Guide', 'Stone Tell', 'Time Oracle', 'Visionary Prophet', 'Waves Oracle']
#
,
'shifter': ['base','Adaptive Shifter', 'Beastkin Berserker', 'Chaos Shifter', 'Cliffwalker Keeper', 'Doppelganger Shifter', 'Dreamstalker', 'Elemental Acolyte', 'Feral Hunter', 'Giant Shifter', 'Lycanthropic Investigator', 'Moonlight Stalker', 'Oozemorph', 'Pack Lord', 'Rageshaper', 'Razorclaw Shifter', 'Saurian Champion', 'Savage Assailant', 'Serpent-Fire Adept', 'Serpentine Bloodline', 'Skinchanger', 'Soul Carver', 'Spellslinger', 'Survivor', 'Tauric Shifter', 'Totem Beast', 'Umbral Blade', 'Verdant Shifter', 'Voidfrost Weaver', 'Watersinger']
#
,
'summoner': ['base','Broodmaster', 'Chthonic Companion', 'Demonic Apostle', 'Ectopic Summoner', 'Elemental Master', 'Gadget Summoner', 'God Caller', 'Harrower', 'Hedge Witch', 'Malconvoker', 'Master Summoner', 'Occultist Summoner', 'Possessed Hand', 'Psychic Summoner', 'Sanguine Angel', 'Soulbound Puppeteer', 'Spirit Summoner', 'Stargazer', 'Synthesist', 'Undead Lord', 'Unlettered Arcanist', 'Void Caller', 'Wild Caller']
#
,
'witch': ['base','Bouda', 'Cartomancer', 'Changeling', 'Child of the Briar', 'Demoniac', 'Elementalist', 'Familiar Adept', 'Fey Caller', 'Gutter Mage', 'Hedge Witch', 'Hex Channeler', 'Magical Child', 'Moon Touched', 'Natural Alchemist', 'Patron Witch', 'Pipehedge Necromancer', 'Sea Witch', 'Silksworn', 'Spirit Binder', 'Spitfire', 'Time Thief', 'Valkyrie', 'Veiled Illusionist', 'Venomfist Adept', 'Witchwarden']
#
,
'arcanist': ['base','Blade Adept', 'Brown-Fur Transmuter', 'Chained', 'Consort', 'Dimensional Occultist', 'Eldritch Font', 'Elemental Master', 'Empyreal', 'False Priest', 'Harrowed Society Mind', 'Occultist', 'Pact Wizard', 'School Savant', 'Scroll Scoundrel', 'Spell Specialist', 'Spirit Binder', 'Twilight Sage']
#
,
'bloodrager': ['base','Crossblooded Rager', 'Draconic Bloodrager', 'Elemental Bloodrager', 'Hateful Rager', 'Id Rager', 'Metamagic Rager', 'Primalist', 'Spelleater', 'Steelblood']
#
,
'brawler': ['base','Battle Dancer', 'Bitter-End Enforcer', 'Boxer', 'Brawler Champion', 'Champion of the Cascade', 'Chirurgeon', 'Clumsy Combatant', 'Cornugon Smash', 'Drunken Brawler', 'Exemplar', 'Falconer', 'Feral Combat Training', 'Free-Style Fighter', 'Grapple Fighter', 'Knockout Artist', 'Martial Artist', 'Mutagenic Mauler', 'Pit Fighter', 'Practiced Tactician', 'Savage Technologist', 'Shield Champion', 'Strangler', 'Strangler of the Occult', 'Street Performer', 'Thunderstriker', 'Torturer', 'Unarmed Fighter', 'Wild Child', 'Winding Path Renegade']
#
,
'hunter': ['base',"Divine Hunter", "Feykiller", "Forester", "Frost Rider", "Gendarme", "Geomancer", "Gloomblade", "Hooded Champion", "Horse Lord", "Infiltrator", "Master of the Wild", "Packmaster", "Planar Hunter", "Reclaimer", "Savage", "Sea Singer", "Spire Defender", "Spirit Channeler", "Spirit Whisperer", "Totemic", "Umbral Stalker", "Veiled Illusionist", "Wild Whisperer"]
#
,
'investigator': ['base',"Empiricist", "Exarch", "Forensic Physician", "Infiltrator", "Lamplighter", "Mastermind", "Questioner", "Sleuth", "Spiritualist Investigator", "Symbiotic Investigator", "Synergist", "Unbreakable Survivor", "Virtuoso Sleuth"]
#
,
'shaman': ['base',"Apothecary", "Chaos Spirit", "Dark Tapestry", "Elemental Ally", "Flamespeaker", "Life Spirit", "Lore Oracle", "Nature Spirit", "Stone Spirit", "Waves Spirit", "Witch Doctor", "Woodsman"]
#
,
'swashbuckler': ['base','Acrobat', 'Buccaneer', 'Daring Infiltrator', 'Daring Champion', 'Flying Blade', 'Inspired Blade', 'Musketeer', 'Mysterious Avenger', 'Picaroon', 'Rondelero duelist', 'Roughrider', 'Serpent Blade', 'Swashbuckler of the Society', 'Vanguard']
#
,
'warpriest': ['base','Arsenal Chaplain', 'Cloistered Cleric', 'Cult Leader', 'Divine Commander', 'Divine Disciple', 'Divine Paragon', 'Divine Strategist', 'Holy Vindicator', 'Iron Priest', 'Sacred Fist', 'Sacred Shield', 'Sacred Sentinel', 'Sanctified Prophet', 'Shielded Fighter', 'Tactical Leader', 'Weapon Adept']
#
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
'conscript':["Alchemy","Athletics","Barrage","Barroom","Beastmastery","Berserker","Boxing","Brute","Dual Wielding","Duelist","Equipment","Fencing","Gladiator","Guardian","Lancer","Open Hand","Scoundrel","Scout","Shield","Sniper","Trap","Warleader","Wrestling"]
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

version = "4/29/23"