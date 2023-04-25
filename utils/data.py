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
regions = ["Tal-falko","Dolestan","Sojoria","Ieso", "Spire", "Feyador", "Esterdragon", "Grundy", "Dust-Cairn"]

races = ['Human','Drow', 'Aasimar', 'Goblin', 'Catfolk', 'Dragonborn', 'Dhampir']
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
    'Dust-Cairn': ['Spear','Natural Weapon', 'Lance', 'Greatsword', 'Rapier']
}


#add all of forests options
languages = ['Abyssal', 'Aklo', 'Aquan', 'Auran', 'Boggard', 'Celestial', 'Common', 'Cyclops', 'Dark Folk', 'Draconic', 'Druidic', 'Drow Sign Language', 'Dwarven', 'Elven', 'Giant', 'Gnoll', 'Gnome', 'Goblin', 'Grippli', 'Halfling', 'Ignan', 'Infernal', 'Kelish', 'Orc', 'Protean', 'Sphinx', 'Sylvan', 'Tengu', 'Terran', 'Treant', 'Undercommon', 'Vegepygmy', 'Vishkanya', 'Wayang']
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
hair_types = ['Curly', 'Wavy', 'Straight', 'Flowing', 'Frizzy', 'Spiky', 'Touseled', 'Unkempt']
eye_colors = ['Amber', 'Blue', 'Brown', 'Grey', 'Green', 'Hazel']
appearance = ['Jewelry', 'Piercings', 'Formal Clothing', 'Ragged', 'Missing Teeth', 'Scar', 'Tattoos', 'Birthmark', 'Bald', 'Braided Hair', 'Twitch', 'Beautiful', 'Ugly']




#add all of forests options
profession = [
'Acrobat',
'Actor/Actress',
'Architect',
'Astronomer',
'Blacksmith',
'Bookbinder',
'Brewer',
'Butcher',
'Carpenter',
'Chef',
'Comedian',
'Crocheter',
'Debater',
'Detective',
'Diplomat',
'Dressmaker/Tailor',
'Electrician',
'Engineer',
'Escape Artist',
'Falconer',
'Farmer',
'Fencer',
'Fire Eater',
'Fisherman',
'Fletcher',
'Florist',
'Forger',
'Glassblower',
'Goldsmith',
'Gossip',
'Graffiti Artist',
'Gymnast',
'Herbalist',
'Hunter',
'Illusionist',
'Jeweler',
'Knife Thrower',
'Leatherworker',
'Linguist',
'Locksmith',
'Lumberjack',
'Makeup Artist',
'Martial Artist',
'Mathematician',
'Mechanic',
'Medium',
'Metalworker',
'Mime',
'Miner',
'Mountaineer',
'Navigator',
'Orator',
'Painter',
'Paraglider',
'Performer',
'Philosopher',
'Photographer',
'Pianist',
'Pirate',
'Poet',
'Potter',
'Puppeteer',
'Rafting Guide',
'Ranger',
'Roofer',
'Sailor',
'Sculptor',
'Singer',
'Skateboarder',
'Skiing/Snowboarding',
'Skydiver',
'Sleight of Hand Artist',
'Smuggler',
'Sniper',
'Snowshoeing',
'Speleologist/Caver',
'Stage Magician',
'Stonecutter',
'Swimmer',
'Tattoo Artist',
'Thief',
'Thrower',
'Trick Roper',
'Veterinarian',
'Ventriloquist',
'Weaponsmith',
'Weaver',
'Whittler',
'Wrestler',
'Writer',
'Yoga Instructor',
'Zookeeper',
'Acupuncturist', 'Animal Trainer', 'Antiques Dealer', 'Astrologer', 'Baker', 'Barista', 'Bartender', 'Beekeeper', 'Bonsai Grower', 'Botanist', 'Calligrapher', 'Cartoonist', 'Ceramicist', 'Chocolatier', 'Climber', 'Collector', 'Colorist', 'Comic Artist', 'Confectioner', 'Cosmetologist', 'Costume Designer', 'Critic', 'Cultural Historian', 'Cutler', 'Dance Instructor', 'Dental Technician', 'Dietitian', 'Diplomatic Courier', 'Director', 'Dog Breeder', 'Entertainer', 'Entrepreneur', 'Event Planner', 'Exotic Dancer', 'Fashion Designer', 'Film Critic', 'Firefighter', 'Fitness Trainer', 'Flair Bartender', 'Flight Attendant', 'Floral Designer', 'Food Critic', 'Forensic Scientist', 'Furniture Maker', 'Game Designer', 'Garden Designer', 'Genealogist', 'Glass Artist', 'Guitarist', 'Hair Stylist', 'Handwriting Expert', 'Headhunter', 'Historian', 'Home Stager', 'Ice Cream Maker', 'Image Consultant', 'Interior Designer', 'Jewelry Maker', 'Juice Maker', 'Karaoke Host', 'Karate Instructor', 'Landscape Architect', 'Lapidary', 'Latte Artist', 'Lighting Designer', 'Lockpick', 'Makeup Instructor', 'Marine Biologist', 'Massage Therapist', 'Mechanical Engineer', 'Mediator', 'Swing Dancing',
'Taxidermy',
'Tea Tasting',
'Technical Writing',
'Theatrical Makeup',
'Toy Making',
'Translation',
'Truffle Hunting',
'Typography',
'Video Editing',
'Virtual Reality Design',
'Visual Effects',
'Wax Sculpting',
'Web Development',
'Wedding Planning',
'Wildlife Biology',
'Wine Tasting'
]

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

archetypes = {

'fighter': ['Tribal Defender', 'Biathlete', 'Road Warrior', 'Aether Soldier', 'Warmachine', 'Harrier', 'Knife Fighter', 'Man-at-Arms', 'Berserker', 'Chain Lasher', 'Challenger', 'Bonded Pet', 'Blade Shifter', 'Technique Master', 'Ironborn', 'Myrmidon', 'Silverblade Hunter', 'Swordsmith', 'Chakram Dervish', 'Quickblade', 'Spellscorn Fighter', 'Coachman', 'Tjuman', 'Pugilist', 'Ructioneer', 'Warrior of the Path', 'Scrapper', 'Aerial Assaulter', 'Spear Fighter', 'Skirmisher', 'Tribal Fighter', 'Venomblade', 'Viking', 'Aquanaut', 'Armiger', 'Defender', 'Lore Warden', 'High Guardian', 'Opportunist Fighter', 'Cyber-Soldier', 'Unbreakable', 'Phalanx Soldier', 'Gladiator', 'Gloomblade', 'Archer', 'Armor Master', 'Blackjack', 'Border Defender', 'Brawler', 'Buckler Duelist', 'Cad', 'Child of War', 'Corsair', 'Crossbowman', 'Dervish of Dawn', 'Dragonheir Scion', 'Dragoon', 'Drill Sergeant', 'Eldritch Guardian', 'Free Hand Fighter', 'Free-Style Fighter', 'Learned Duelist', 'Titan Fighter', 'Seasoned Commander', 'Martial Master', 'Mobile Fighter', 'Mutation Warrior', 'Pack Mule', 'Polearm Master', 'Relic Master', 'Roughrider', 'Savage Warrior', 'Sensate', 'Shielded Fighter', 'Siegebreaker', 'Steelbound Fighter', 'Swordlord', 'Tactician', 'Thunderstriker', 'Tower Shield Specialist', 'Trench Fighter', 'Two-Handed Fighter', 'Two-Weapon Warrior', 'Unarmed Fighter', 'Vengeful Hunter', 'Viking', 'Weapon Bearer Squire', 'Weapon Master', 'Warshade', 'Kappa-Bushi', 'Peltast', 'Tengubushi', 'Yakuza Bushi', 'Dragon Warrior']
,
#
'barbarian': ['Armored Hulk','Beastkin Berserker','Blooded Arcanist','Breaker','Brutal Pugilist','Cannibal','Chaos Totem','Dreadnought','Elemental Kin','Fated Champion','Feral Gnasher','Flesheater','Furyborn','Goliath Druid','Hateful Rager','Hurler','Invulnerable Rager','Lion Blade','Marauder','Mooncursed','Mounted Fury','Pack Rager','Primal Hunter','Primalist','Raging Cannibal','Raging Cyclone','Raging Drunk','Raging Flame','Raging Hurler','Raging Tactician','Savage Barbarian','Scarred Rager','Sea Reaver','Shaman','Skeletal Champion','Spell Sunderer','Steel-Breaker','Superstitious','Survivor','Titan Mauler','Totem Warrior','True Primitive','Unchained Rager','Urban Barbarian','Wild Rager']
,
#
'druid': ['Agathiel', 'Animal Shaman', 'Aquatic Druid', 'Arboreal Grappler', 'Archdruid', 'Blacksnake', 'Blazoned Tracker', 'Blight Druid', 'Blind Singer', 'Blightwarden', 'Child of the Moon', 'Cleric of the Green', 'Death Druid', 'Defender of the True World', 'Dragon Shaman', 'Dreamspeaker', 'Elemental Ally', 'Elemental Ascetic', 'Elemental Druid', 'Emberkin', 'Enlightened Druid', 'Fanglord', 'Feral Child', 'Fey Caller', 'Fist of the Forest', 'Flame Keeper', 'Frostburn Warden', 'Geisha', 'Geomancer', 'Green Faith Acolyte', 'Green Scourge', 'Greenstalker', 'Guardian of the Wild', 'Harrow Warden', 'Hedge Witch', 'Hooded Champion', 'Ice Sentinel', 'Infiltrator', 'Inquisitor of the Elk', 'Inquisitor of the Raven', 'Inquisitor of the Water', 'Jungle Druid', 'Lion Shaman', 'Lithic', 'Mad Prophet', 'Mammoth Rider', 'Master of Many Forms', 'Master of Storms', 'Mooncaller', 'Mooncursed', 'natures Fang', 'natures Whispers', 'Nature-Bonded Magus', 'Necrologist', 'Pack Lord', 'Pain Taster', 'Pale Stranger', 'Plant Master', 'Polar Midnight', 'Powerful Shapechanger', 'Rage Prophet', 'Ravenlord', 'Reincarnated Druid', 'River Druid', 'Saurian Shaman', 'Sea Reaver', 'Serpent-Fire Adept', 'Serpentfire', 'Shark Shaman', 'Shapeshifter', 'Shark Shaman', 'Storm Druid', 'Stormwalker', 'Street Shaman', 'Swamp Druid', 'Tamer of Beasts', 'Teisatsu', 'Theologian', 'Thornwarden', 'Thundercaller', 'Totemic Demonslayer', 'Tribal Shaman', 'Tunnel Rat', 'Undead Lord', 'Urban Druid', 'Verdant Lord', 'Verminous Hunter', 'Visionary Seeker', 'Volcano Priest', 'Vulture Shaman', 'Warshaper', 'Wild Rager', 'Wild Whisperer', 'Wildfire Heart', 'Winter Witch', 'Wolf Shaman', 'Woodland Skirmisher', 'World Walker', 'Wyrm Singer' ]
,
#
'cleric': ['Angelfire Apostle', 'Anger Inquisition', 'Aquatic Druid', 'Arcanist', 'Atheist', 'Battle Priest', 'Chaos Channeler', 'Cloistered Cleric', 'Crusader', 'Divine Strategist', 'Evangelist', 'Exalted', 'Feral Hunter', 'Inheritors Crusader', 'Liturgical Mage', 'Merciful Healer', 'Necromancer', 'Planar Oracle', 'Ravener Hunter', 'Sanguine Angel', 'Separatist', 'Shaman', 'Theologian', 'Undead Lord', 'Varisian Pilgrim', 'Visionary Prophet']
,
#
'rogue':  ['Acrobat', 'Bandit', 'Beastmaster', 'Beguiler', 'Burglar', 'Charlatan', 'Chirurgeon', 'Circus Performer', 'Cloaked Dancer', 'Cloistered Cleric', 'Commando', 'Con Artist', 'Counterfeit Mage', 'Court Fool', 'Cutpurse', 'Daggermark Poisoner', 'Dandy', 'Dark Delver', 'Deep Walker', 'Demagogue', 'Dervish of Dawn', 'Eldritch Scoundrel', 'False Medium', 'Fast Hands', 'Gang Leader', 'Gloomblade', 'Guerrilla', 'Guild Agent', 'Guild Poisoner', 'Hidden Priest', 'Highwayman', 'Hooded Champion', 'Infiltrator', 'Knife Master', 'Liberator', 'Master Spy', 'Mouser', 'Natural Alchemist', 'Noble Fencer', 'Phantom Thief', 'Pilferer', 'Pirate', 'Poisoner', 'Rake', 'Rapscallion', 'Ratcatcher', 'Ringleader', 'Saboteur', 'Sandman', 'Sapper', 'Savage Skirmisher', 'Scavenger', 'Scout', 'Shadowdancer', 'Shadow Rager', 'Sleuth', 'Sniper', 'Spy', 'Stalker', 'Streetfighter', 'Survivalist', 'Swordmaster', 'Thief Acrobat', 'Thug', 'Trapsmith', 'Underground Chemist', 'Vexing Dodger', 'Vigilante', 'Wasp', 'Watersinger', 'Wild Child', 'Zealot']
,
#
'ranger':  ['Airborne Ambusher', 'Arboreal Ranger', 'Battle Scout', 'Beastmaster', 'Blightwarden', 'Bow Nomad', 'Cavalier', 'Child of Acavna and Amaznen', 'Deep Walker', 'Divine Marksman', 'Dragon Hunter', 'Duskwarden', 'Falconer', 'Favored Enemy (aquatic)', 'Favored Enemy (dungeon)', 'Favored Enemy (forest)', 'Favored Enemy (giant)', 'Favored Enemy (magical beast)', 'Favored Enemy (plant)', 'Favored Enemy (undead)', 'Frost Tusk', 'Geomancer', 'Ghost Hunter', 'Giant Killer', 'Guide', 'Harrow Warden', 'Hooded Champion', 'Horse Lord', 'Horizon Walker', 'Infiltrator', 'Initiate of the Hunt', 'Liberator', 'Lion Blade', 'Living Monolith', 'Master of Many Forms', 'Natural Warrior', 'Nature Warden', 'Pack Lord', 'Pathfinder Chronicler', 'Polearm Master', 'Reaper of Secrets', 'Sable Company Marine', 'Savage Skirmisher', 'Sea Dog', 'Skirmisher', 'Stormwalker', 'Strider', 'Swift Hunter', 'Terramancer', 'Thundercaller', 'Trapper', 'Treantmonk (Druid/Ranger)', 'Trick Shot', 'Trickster', 'Two-Handed Fighter', 'Urban Ranger', 'Verdant Sorcerer', 'Wild Shadow', 'Wild Stalker', 'Witch Hunter', 'Woodland Skirmisher', 'World Walker']
,
#
#
'paladin' : ['Angelic', 'Blade of Mercy', 'Chosen One', 'Divine Defender', 'Divine Guardian', 'Divine Hunter', 'Divine Paragon', 'Divine Scion', 'Divine Servitor', 'Divine Strategist', 'Enlightened Paladin', 'Eternal Hope', 'Gray Paladin', 'Holy Gun', 'Hospitaler', 'Oathbound Paladin', 'Oath of Vengeance', 'Paladin of Freedom', 'Sacred Servant', 'Shining Knight', 'Templar']

#
#
}

                    #Path of war classes

version = "1.1.4"