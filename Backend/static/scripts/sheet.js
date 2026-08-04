// Read-only pf1-style character sheet, rendered client-side from the generator's JSON.
// Everything renders through renderSheet(data) so later interactivity (rolls, HP tracking,
// buff toggles) can hook onto the same DOM + localStorage copy without rearchitecting.

(function () {
    'use strict';

    const CHAR_KEY = 'sheet.characterData';
    const FORM_KEY = 'sheet.formData';

    // ---------------------------------------------------------------- form option data
    // Mirrors the Foundry module's generator dialog (button.js) so both clients send the
    // same values to /update_character_data.
    const REGIONS = ['Random', 'Tal-falko', 'Dolestan', 'Sojoria', 'Ieso', 'Spire', 'Feyador',
        'Esterdragon', 'Grundykin Damplands', 'Dust Cairn', 'Kaeru no Tochi'];
    // The two labels that are not the region's canonical key (utils/data.py::regions). The backend
    // aliases them anyway, for the module and for saved form data it cannot upgrade — but a client
    // in this repo sends the key, so the alias stays a shim rather than a dependency.
    const REGION_VALUES = { 'Random': '', 'Grundykin Damplands': 'Grundy', 'Dust Cairn': 'Dust-Cairn' };
    const RACES = ['Random', 'Dwarf', 'Elf', 'Gnome', 'Half-Elf', 'Halfling', 'Half-Orc', 'Human',
        'Aasimar', 'Aquatic Elf', 'Catfolk', 'Changeling', 'Dhampir', 'Drow', 'Fetchling',
        'Gathlain', 'Ghoran', 'Gillman', 'Goblin', 'Grippli', 'Hobgoblin', 'Ifrit', 'Kitsune',
        'Kobold', 'Locathah', 'Merfolk', 'Monkey Goblin', 'Nagaji', 'Orc', 'Oread', 'Ratfolk',
        'Sahuagin', 'Skinwalker', 'Strix', 'Svirfneblin', 'Sylph', 'Syrinx', 'Tengu', 'Tiefling',
        'Triaxian', 'Triton', 'Undine', 'Vanara', 'Vine Leshy', 'Vishkanya', 'Wayang', 'Wyrwood',
        'Wyvaran', 'Yaddithian'];
    // Unlike the Foundry module, the web sheet has no compendium constraint, so Stalker and
    // Zealot are selectable here even while they stay out of the module's class list.
    const CLASSES = ['Random', 'Alchemist', 'Antipaladin', 'Arcanist', 'Barbarian',
        'Barbarian (Unchained)', 'Bard', 'Bloodrager', 'Brawler', 'Cavalier', 'Cleric', 'Druid',
        'Fighter', 'Gunslinger', 'Hunter', 'Inquisitor', 'Investigator', 'Magus', 'Monk',
        'Monk (Unchained)', 'Ninja', 'Oracle', 'Paladin', 'Ranger', 'Rogue', 'Rogue (Unchained)',
        'Samurai', 'Shaman', 'Shifter', 'Skald', 'Slayer', 'Sorcerer', 'Summoner',
        'Summoner (Unchained)', 'Swashbuckler', 'Vigilante', 'Warpriest', 'Witch', 'Wizard',
        'Warlord', 'Warder', 'Harbinger', 'Mystic', 'Medic', 'Stalker', 'Zealot'];
    const DEITIES = ['random', 'Abadar', 'Achaekek', 'Ahriman', 'Alazhra', 'Alseta', 'Apsu',
        'Arazni', 'Asmodeus', 'Besmara', 'Calistria', 'Cayden Cailean', 'Desna', 'Easivra',
        'Erastil', 'Erecura', 'Gorum', 'Gozreh', 'Groetus', 'Hanspur', 'Iomedae', 'Irori',
        'Kurgess', 'Lamashtu', 'Lissala', 'Nethys', 'Norgorber', 'Pharasma', 'Rovagug',
        'Sarenrae', 'Shelyn', 'Torag', 'Urgathoa', 'Zon-Kuthon', 'Zyphus'];

    // Good-save progressions per class, extracted from the pf1e_random_char_generator module's
    // every_class.json (pf1 + pf1-pow compendium export). Stalker/Zealot are absent from that
    // compendium; their entries follow the d20pfsrd Path of War class tables.
    // FALLBACK ONLY for cached payloads without save_bases — the authoritative copy lives in
    // Backend/utils/data.py (good_saves), which stacks saves per class server-side. Keep in sync.
    const GOOD_SAVES = {
        'alchemist': ['fort', 'ref'], 'antipaladin': ['fort', 'will'], 'arcanist': ['will'],
        'barbarian': ['fort'], 'barbarian (unchained)': ['fort'], 'bard': ['ref', 'will'],
        'bloodrager': ['fort'], 'brawler': ['fort', 'ref'], 'cavalier': ['fort'],
        'cleric': ['fort', 'will'], 'druid': ['fort', 'will'], 'fighter': ['fort'],
        'gunslinger': ['fort', 'ref'], 'harbinger': ['fort', 'will'], 'hunter': ['fort', 'ref'],
        'inquisitor': ['fort', 'will'], 'investigator': ['ref', 'will'],
        'kineticist': ['fort', 'ref'], 'magus': ['fort', 'will'], 'medic': ['fort', 'will'],
        'medium': ['will'], 'mesmerist': ['ref', 'will'], 'monk': ['fort', 'ref', 'will'],
        'monk (unchained)': ['fort', 'ref'], 'mystic': ['will'], 'ninja': ['ref'],
        'occultist': ['fort', 'will'], 'oracle': ['will'], 'paladin': ['fort', 'will'],
        'psychic': ['will'], 'ranger': ['fort', 'ref'], 'rogue': ['ref'],
        'rogue (unchained)': ['ref'], 'samurai': ['fort'], 'shaman': ['will'],
        'shifter': ['fort', 'ref'], 'skald': ['fort', 'will'], 'slayer': ['fort', 'ref'],
        'sorcerer': ['will'], 'spiritualist': ['fort', 'will'], 'stalker': ['will'],
        'summoner': ['will'], 'summoner (unchained)': ['will'], 'swashbuckler': ['ref'],
        'vigilante': ['ref', 'will'], 'warder': ['fort', 'will'], 'warlord': ['fort'],
        'warpriest': ['fort', 'will'], 'witch': ['will'], 'wizard': ['will'],
        'zealot': ['fort', 'will'],
    };

    // ---------------------------------------------------------------- tiny DOM helpers
    function h(tag, cls, content) {
        const el = document.createElement(tag);
        if (cls) el.className = cls;
        if (content !== undefined && content !== null) {
            if (content instanceof Node) el.appendChild(content);
            else el.textContent = String(content);
        }
        return el;
    }

    // Descriptions come from our own backend / game data, so rendering them as HTML is fine.
    function htmlBlock(cls, html) {
        const el = h('div', cls);
        el.innerHTML = html;
        return el;
    }

    function details(summaryText, bodyHtml, cls) {
        const d = h('details', cls);
        d.appendChild(h('summary', null, summaryText));
        if (bodyHtml) d.appendChild(htmlBlock('desc', bodyHtml));
        return d;
    }

    function section(title, cls) {
        const sec = h('section', 'sheet-section' + (cls ? ' ' + cls : ''));
        sec.appendChild(h('h2', null, title));
        const body = h('div', 'section-body');
        sec.appendChild(body);
        return { sec, body };
    }

    function kv(body, label, value) {
        const row = h('div', 'kv');
        row.appendChild(h('span', 'k', label));
        row.appendChild(h('span', 'v', value));
        body.appendChild(row);
    }

    const titleCase = (s) => String(s).replace(/\b\w/g, (c) => c.toUpperCase());
    const mod = (score) => Math.floor((Number(score) - 10) / 2);
    const fmt = (n) => (n >= 0 ? '+' + n : String(n));
    const toInt = (v) => {
        const n = parseInt(v, 10);
        return Number.isFinite(n) ? n : null;
    };
    // true only for non-empty arrays/objects (strings like 'N/A' don't count)
    const nonEmpty = (v) => Array.isArray(v) ? v.length > 0
        : Boolean(v && typeof v === 'object' && Object.keys(v).length > 0);

    // ---------------------------------------------------------------- sheet sections
    function renderHeader(data) {
        const head = h('div', 'sheet-header');
        head.appendChild(h('h1', 'char-name', data.character_full_name || 'Unnamed'));
        const arch = data.archetype1 ? ` (${data.archetype1})` : '';
        // multiclass payloads carry a classes array ("Fighter 6 / Wizard 4"); older cached
        // payloads fall back to the legacy c_class/c_class_2 + level fields
        let clsLine;
        if (Array.isArray(data.classes) && data.classes.length) {
            clsLine = data.classes.map((c) => `${c.display || titleCase(c.name)} ${c.level}`).join(' / ') + arch;
        } else {
            const cls2 = data.c_class_2 ? ' / ' + titleCase(data.c_class_2) : '';
            clsLine = `${(data.c_class_display || data.c_class || '?')}${cls2}${arch} ${data.level ?? '?'}`;
        }
        const line = [
            `${data.chosen_race || '?'} ${clsLine}`,
            data.alignment,
            data.gender,
            Array.isArray(data.deity_name) ? data.deity_name.join(', ') : data.deity_name,
            data.region,
        ].filter(Boolean).join(' · ');
        head.appendChild(h('p', 'char-line', line));
        const fluff = [
            data.age_number != null ? `Age ${data.age_number}` : null,
            data.height_number, data.weight_number != null ? `${data.weight_number} lbs` : null,
            Array.isArray(data.language_text) && data.language_text.length
                ? 'Languages: Common, ' + data.language_text.join(', ') : null,
        ].filter(Boolean).join(' · ');
        if (fluff) head.appendChild(h('p', 'char-line dim', fluff));
        return head;
    }

    function renderAbilities(data) {
        const wrap = h('div', 'ability-row');
        for (const ab of ['str', 'dex', 'con', 'int', 'wis', 'cha']) {
            const score = data[ab];
            if (score == null) continue;
            const box = h('div', 'ability-box' + (data.main_stat === ab ? ' main-stat' : ''));
            box.appendChild(h('div', 'ab-name', ab.toUpperCase()));
            box.appendChild(h('div', 'ab-score', score));
            box.appendChild(h('div', 'ab-mod', fmt(mod(score))));
            wrap.appendChild(box);
        }
        return wrap;
    }

    function saveBonus(level, good) {
        return good ? 2 + Math.floor(level / 2) : Math.floor(level / 3);
    }

    function renderCombat(data) {
        const { sec, body } = section('Combat (base estimates — before feats, buffs & items)', 'combat');
        const level = Number(data.level) || 0;
        const bab = Number(data.bab_total) || 0;
        const strM = mod(data.str), dexM = mod(data.dex), conM = mod(data.con), wisM = mod(data.wis);

        const armorAc = toInt(data.armor_ac) ?? 0;
        const shieldAc = toInt(data.shield_ac) ?? 0;
        const maxDex = toInt(data.armor_max_dex_bonus);
        const effDex = maxDex === null ? dexM : Math.min(dexM, maxDex);

        kv(body, 'HP', data.Total_HP ?? '?');
        kv(body, 'Initiative', fmt(dexM));
        kv(body, 'Speed', (data.land_speed ?? '?') + ' ft');
        kv(body, 'BAB', fmt(bab));
        kv(body, 'Melee / Ranged', `${fmt(bab + strM)} / ${fmt(bab + dexM)}`);
        kv(body, 'CMB / CMD', `${fmt(bab + strM)} / ${10 + bab + strM + dexM}`);
        kv(body, 'AC', `${10 + armorAc + shieldAc + effDex} (touch ${10 + effDex}, flat-footed ${10 + armorAc + shieldAc})`);

        // save_bases comes stacked per class from the backend (multiclass-correct); the
        // GOOD_SAVES table below is only the fallback for cached payloads that predate it
        if (data.save_bases && typeof data.save_bases === 'object') {
            const sb = data.save_bases;
            kv(body, 'Saves',
                `Fort ${fmt((Number(sb.fort) || 0) + conM)}, Ref ${fmt((Number(sb.ref) || 0) + dexM)}, Will ${fmt((Number(sb.will) || 0) + wisM)}`);
            return sec;
        }
        const goods = GOOD_SAVES[String(data.c_class || '').toLowerCase()];
        if (goods && level) {
            const s = (name, abM) => fmt(saveBonus(level, goods.includes(name)) + abM);
            let saves = `Fort ${s('fort', conM)}, Ref ${s('ref', dexM)}, Will ${s('will', wisM)}`;
            if (data.c_class_2) saves += ' (multiclass: first class only)';
            kv(body, 'Saves', saves);
        } else {
            kv(body, 'Saves', 'unknown class progression');
        }
        return sec;
    }

    function renderGear(data) {
        const { sec, body } = section('Gear & Wealth');
        if (data.weapon_name && data.weapon_name.trim()) {
            let w = data.weapon_name;
            if (nonEmpty(data.weapon_enhancement_chosen_list)) w += ' [' + data.weapon_enhancement_chosen_list.join(', ') + ']';
            kv(body, 'Weapon', w);
        }
        if (data.armor_name && data.armor_name.trim()) {
            let a = data.armor_name;
            if (nonEmpty(data.armor_enhancement_chosen_list)) a += ' [' + data.armor_enhancement_chosen_list.join(', ') + ']';
            const bits = [
                data.armor_ac ? `+${data.armor_ac} AC` : null,
                data.armor_max_dex_bonus?.trim?.() ? `max Dex ${data.armor_max_dex_bonus}` : null,
                data.armor_armor_check_penalty?.trim?.() ? `ACP ${data.armor_armor_check_penalty}` : null,
                data.armor_spell_failure ? `ASF ${data.armor_spell_failure}%` : null,
            ].filter(Boolean).join(', ');
            kv(body, 'Armor', bits ? `${a} (${bits})` : a);
        }
        if (data.shield_name && data.shield_name.trim()) {
            let s = data.shield_name;
            if (nonEmpty(data.shield_enhancement_chosen_list)) s += ' [' + data.shield_enhancement_chosen_list.join(', ') + ']';
            kv(body, 'Shield', s);
        }
        if (data.gold != null) kv(body, 'Gold', `${data.gold} gp` + (data.platnium ? ` (${data.platnium} pp)` : ''));
        if (nonEmpty(data.equipment_list)) {
            const ul = h('ul', 'plain-list');
            for (const item of data.equipment_list) {
                const name = typeof item === 'string' ? item : (item?.name ?? JSON.stringify(item));
                const d = data.equip_descrip?.[name];
                const li = ul.appendChild(h('li', null, null));
                const unplaced = data.item_changes_dict?.[name]?.unplaced;
                if (d || (unplaced && unplaced.length)) {
                    const det = details(name, d);
                    if (unplaced && unplaced.length) {
                        const fx = h('div', 'desc item-effects');
                        fx.appendChild(h('strong', null, 'Effects: '));
                        for (const text of unplaced) fx.appendChild(h('div', null, text));
                        det.appendChild(fx);
                    }
                    li.appendChild(det);
                } else {
                    li.appendChild(h('span', null, name));
                }
            }
            body.appendChild(ul);
        }
        return body.childNodes.length ? sec : null;
    }

    function renderSkills(data) {
        let ranks = data.skill_ranks;
        if (typeof ranks === 'string') { try { ranks = JSON.parse(ranks); } catch { ranks = null; } }
        if (!nonEmpty(ranks)) return null;
        const { sec, body } = section('Skills');
        const table = h('table', 'skills-table');
        const unlockSkill = (data.skill_unlock?.base_skill || '').toLowerCase();
        for (const [name, r] of Object.entries(ranks).sort((a, b) => a[0].localeCompare(b[0]))) {
            if (!r) continue;
            const tr = h('tr', name.toLowerCase() === unlockSkill ? 'unlocked' : null);
            tr.appendChild(h('td', null, titleCase(name) + (name.toLowerCase() === unlockSkill ? ' ★' : '')));
            tr.appendChild(h('td', 'num', r));
            table.appendChild(tr);
        }
        body.appendChild(table);
        if (data.skill_unlock?.skill) {
            const u = data.skill_unlock;
            const tiers = Object.entries(u.unlock || {})
                .map(([lv, txt]) => `<p><strong>${lv} ranks:</strong> ${txt}</p>`).join('');
            body.appendChild(details(`★ Skill Unlock: ${u.skill}`, tiers));
        }
        if (nonEmpty(data.profession_ranks)) {
            const t2 = h('table', 'skills-table professions');
            for (const p of data.profession_ranks) {
                const tr = h('tr');
                tr.appendChild(h('td', null, p.skill_label || p.name));
                tr.appendChild(h('td', 'num', `${p.ranks}/${p.cap}`));
                t2.appendChild(tr);
            }
            body.appendChild(h('h3', null, 'Professions'));
            body.appendChild(t2);
            if (data.profession_pool != null) kv(body, 'Profession rank pool', data.profession_pool);
        }
        return sec;
    }

    function featItem(name, descSource, label) {
        const text = label ? `${name} ${label}` : name;
        const desc = descSource?.[name];
        const li = h('li');
        li.appendChild(desc ? details(text, desc) : h('span', null, text));
        return li;
    }

    function renderFeats(data) {
        const descs = data.homebrew_feat_desc_dict || {};
        const groups = [
            ['Feats', data.feats, null],
            ['Class Feats', data.class_feats, data.class_feat_labels],
            ['Story Feats', data.story_feats, null],
            ['Flaw Feats', data.flaw_feats, null],
            ['Flavor Feats', data.flavor_feats, null],
            ['Teamwork Feats', data.teamwork_feat_labels, null],
            ['Bloodline Feats', data.bloodline_feats, data.bloodline_feat_labels],
            ['Trainer Feats', data.trainer_feats, data.trainer_feat_labels],
            ['Profession Feats', data.profession_feats, null],
            ['Sphere Feats', data.sphere_feats, null],
            ['Martial Training', data.mt_feats, null],
        ].filter(([, list]) => nonEmpty(list));
        if (!groups.length) return null;
        const { sec, body } = section('Feats');
        for (const [title, list, labels] of groups) {
            body.appendChild(h('h3', null, title));
            const ul = h('ul', 'plain-list');
            list.forEach((f, i) => {
                const label = labels?.[i] ? `(${String(labels[i]).replace(/^\(|\)$/g, '')})` : null;
                const descSource = title === 'Profession Feats'
                    ? { ...descs, ...(data.profession_feat_desc || {}) } : descs;
                ul.appendChild(featItem(f, descSource, label));
            });
            body.appendChild(ul);
        }
        return sec;
    }

    function renderTraits(data) {
        const groups = [
            ['Traits', data.selected_traits],
            ['Background', data.background_traits],
            ['Sphere Traits', data.sphere_traits],
            ['Flaws', data.flaw],
        ].filter(([, l]) => nonEmpty(l));
        if (!groups.length) return null;
        const { sec, body } = section('Traits & Flaws');
        for (const [title, list] of groups) {
            body.appendChild(h('h3', null, title));
            const ul = h('ul', 'plain-list');
            list.forEach((t) => ul.appendChild(h('li', null, t)));
            body.appendChild(ul);
        }
        return sec;
    }

    function renderClassFeatures(data) {
        const list = data.class_ability;
        const items = [];
        if (nonEmpty(list)) {
            for (const entry of list) {
                // entries look like "arcane school_wizard" -> name + owning class
                const cut = String(entry).lastIndexOf('_');
                const name = cut > 0 ? entry.slice(0, cut) : entry;
                const desc = data.class_ability_desc?.[name] || data.class_features?.[name]?.description;
                items.push([titleCase(name), desc]);
            }
        }
        for (const pa of data.profession_ability_items || []) items.push([pa.name, pa.description]);
        if (!items.length) return null;
        const { sec, body } = section('Class Features & Abilities');
        const extras = [
            ['Wizard School', data.school !== 'N/A' ? data.school : null],
            ['Opposition Schools', nonEmpty(data.opposing_school) ? data.opposing_school.join(', ') : null],
            ['Bloodline', data.bloodline && data.bloodline !== 'N/A' ? data.bloodline : null],
            ['Domains', nonEmpty(data.full_domain) ? data.full_domain.join(', ') : null],
        ];
        for (const [k, v] of extras) if (v) kv(body, k, titleCase(String(v)));
        const ul = h('ul', 'plain-list');
        for (const [name, desc] of items) ul.appendChild(h('li', null, null)).appendChild(desc ? details(name, desc) : h('span', null, name));
        body.appendChild(ul);
        return sec;
    }

    function renderSpellBlock(body, perDay, known, lists, casterLine) {
        if (casterLine) kv(body, 'Caster progression', casterLine);
        if (nonEmpty(perDay)) {
            const table = h('table', 'spell-table');
            const hd = h('tr');
            ['Spell Level', 'Per Day', 'Known'].forEach((t) => hd.appendChild(h('th', null, t)));
            table.appendChild(hd);
            perDay.forEach((d, i) => {
                const tr = h('tr');
                tr.appendChild(h('td', null, i));
                tr.appendChild(h('td', 'num', d));
                tr.appendChild(h('td', 'num', known?.[i] ?? '—'));
                table.appendChild(tr);
            });
            body.appendChild(table);
        }
        if (nonEmpty(lists)) {
            lists.forEach((spells, i) => {
                if (!nonEmpty(spells)) return;
                body.appendChild(details(`Level ${i} spells (${spells.length})`,
                    '<p>' + spells.join(', ') + '</p>', 'spell-list'));
            });
        }
    }

    function renderSpells(data) {
        // multiclass payloads carry one spellbook per caster class; older cached payloads fall
        // back to the legacy single-book top-level fields
        if (Array.isArray(data.spellbooks) && data.spellbooks.length) {
            const books = data.spellbooks.filter((b) =>
                nonEmpty(b.spells_per_day_list) || nonEmpty(b.spell_list_choose_from));
            if (!books.length) return null;
            const { sec, body } = section('Spellcasting');
            // payload arrives level-sorted: book 0 = the Foundry primary book, then secondary, ...
            const SLOT_LABELS = ['Primary', 'Secondary', 'Tertiary'];
            books.forEach((book, bi) => {
                if (books.length > 1 || data.spellbooks.length > 1) {
                    const slot = SLOT_LABELS[bi] ? `${SLOT_LABELS[bi]}: ` : '';
                    body.appendChild(h('h3', null,
                        `${slot}${book.display || titleCase(book.name)} ${book.level} — Caster Level ${book.casting_level_num ?? '?'}`));
                }
                renderSpellBlock(body, book.spells_per_day_list, book.spells_known_list,
                    book.spell_list_choose_from, book.casting_level_string);
            });
            return sec;
        }
        const perDay = data.day_list, known = data.known_list, lists = data.spell_list_choose_from;
        if (!nonEmpty(perDay) && !nonEmpty(lists)) return null;
        const { sec, body } = section('Spellcasting');
        renderSpellBlock(body, perDay, known, lists, data.casting_level_str_foundry);
        return sec;
    }

    function renderPathOfWar(data) {
        if (!(Number(data.initiator_level) > 0) && !nonEmpty(data.martial_disciplines)) return null;
        const { sec, body } = section('Path of War');
        kv(body, 'Initiator Level', data.initiator_level);
        kv(body, 'Initiation Stat', (data.initiation_stat || '').toUpperCase());
        if (nonEmpty(data.martial_disciplines)) kv(body, 'Disciplines', data.martial_disciplines.join(', '));
        if (nonEmpty(data.maneuvers_known_list)) {
            kv(body, 'Maneuvers Known', data.maneuvers_known_list.map((n, i) => `L${i + 1}: ${n}`).join(', '));
        }
        const descs = data.maneuvers_desc_dict || {};
        const maneuverLine = (name) => {
            const d = descs[name];
            const summary = d && typeof d === 'object' ? d.description : d;
            return summary ? details(name, summary) : h('span', null, name);
        };
        if (nonEmpty(data.maneuvers_readied_names)) {
            body.appendChild(h('h3', null, 'Readied Maneuvers'));
            data.maneuvers_readied_names.forEach((names, i) => {
                if (!nonEmpty(names)) return;
                const wrap = h('div', 'maneuver-level');
                wrap.appendChild(h('strong', null, `Level ${i + 1}: `));
                const ul = h('ul', 'plain-list');
                names.forEach((n) => ul.appendChild(h('li', null, null)).appendChild(maneuverLine(n)));
                wrap.appendChild(ul);
                body.appendChild(wrap);
            });
        }
        if (nonEmpty(data.stances_chosen)) {
            body.appendChild(h('h3', null, 'Stances'));
            const ul = h('ul', 'plain-list');
            data.stances_chosen.forEach((s) => ul.appendChild(h('li', null, null)).appendChild(maneuverLine(s)));
            body.appendChild(ul);
        }
        return sec;
    }

    function renderSpheres(data) {
        const talents = [...(data.magic_talent_items || []), ...(data.combat_talent_items || [])];
        if (!nonEmpty(data.spheres_chosen) && !talents.length) return null;
        const { sec, body } = section('Spheres');
        if (data.sphere_mana_pool) kv(body, 'Spell Points', data.sphere_mana_pool);
        const ct = data.casting_tradition || {};
        if (ct.casting_ability_modifier) kv(body, 'Casting Ability', ct.casting_ability_modifier);
        if (nonEmpty(data.spheres_chosen)) {
            kv(body, 'Spheres', data.spheres_chosen
                .map((s) => `${s.sphere} (${s.system})`).join(', '));
        }
        const detailList = (title, names, detailArr) => {
            if (!nonEmpty(names)) return;
            body.appendChild(h('h3', null, title));
            const ul = h('ul', 'plain-list');
            const byName = {};
            (detailArr || []).forEach((d) => { if (d?.name) byName[d.name] = d.description; });
            names.forEach((n) => ul.appendChild(h('li', null, null))
                .appendChild(byName[n] ? details(n, byName[n]) : h('span', null, n)));
            body.appendChild(ul);
        };
        detailList('Tradition Drawbacks', data.sphere_drawbacks, ct.drawbacks_detail);
        detailList('Tradition Boons', data.sphere_boons, ct.boons_detail);
        if (talents.length) {
            body.appendChild(h('h3', null, 'Talents'));
            const bySphere = {};
            for (const t of talents) (bySphere[t.sphere || 'Other'] ??= []).push(t);
            for (const [sphere, ts] of Object.entries(bySphere)) {
                const wrap = h('div', 'maneuver-level');
                wrap.appendChild(h('strong', null, sphere + ': '));
                const ul = h('ul', 'plain-list');
                ts.forEach((t) => ul.appendChild(h('li', null, null)).appendChild(
                    t.description ? details(t.name + (t.advanced ? ' (advanced)' : ''), t.description)
                        : h('span', null, t.name)));
                wrap.appendChild(ul);
                body.appendChild(wrap);
            }
        }
        return sec;
    }

    function renderDescription(data) {
        const { sec, body } = section('Description & Personality');
        const hair = [data.hair_type, data.hair_color].flat().filter(Boolean).join(' ');
        if (hair) kv(body, 'Hair', hair);
        if (nonEmpty(data.eye_color)) kv(body, 'Eyes', [].concat(data.eye_color).join(', '));
        if (nonEmpty(data.appearance)) kv(body, 'Appearance', [].concat(data.appearance).join(', '));
        if (nonEmpty(data.personality_traits)) kv(body, 'Personality', data.personality_traits.join(', '));
        if (nonEmpty(data.mannerisms)) kv(body, 'Mannerisms', data.mannerisms.join(', '));
        if (nonEmpty(data.professions)) kv(body, 'Professions', data.professions.join(', '));
        if (data.craft_type) kv(body, 'Craft', data.craft_type);
        const family = [data.parents, data.older_brothers, data.younger_brothers,
            data.older_sisters, data.younger_sisters]
            .map((s) => String(s || '').trim()).filter((s) => s && !/you have 0/.test(s)).join('; ');
        if (family) kv(body, 'Family', family);
        return body.childNodes.length ? sec : null;
    }

    function renderBackstory(data) {
        if (!data.backstory) return null;
        const { sec, body } = section('Backstory');
        String(data.backstory).split(/\n+/).forEach((p) => { if (p.trim()) body.appendChild(h('p', null, p)); });
        return sec;
    }

    function renderSheet(data) {
        const sheet = document.getElementById('sheet');
        sheet.innerHTML = '';
        if (!data || typeof data !== 'object' || data.error) {
            sheet.appendChild(h('p', 'placeholder error', data?.error ? 'Backend error: ' + data.error : 'No character data.'));
            return;
        }
        sheet.appendChild(renderHeader(data));
        sheet.appendChild(renderAbilities(data));
        const grid = h('div', 'sheet-grid');
        for (const renderer of [renderCombat, renderGear, renderSkills, renderFeats, renderTraits,
            renderClassFeatures, renderSpells, renderPathOfWar, renderSpheres,
            renderDescription, renderBackstory]) {
            const secEl = renderer(data);
            if (secEl) grid.appendChild(secEl);
        }
        sheet.appendChild(grid);
        if (data.generator_version) sheet.appendChild(h('p', 'dim footer', 'generator ' + data.generator_version));
    }

    // Exposed for console debugging and future interactive layers.
    window.renderSheet = renderSheet;

    // ---------------------------------------------------------------- generate form
    function fillSelect(sel, options, valueFn) {
        for (const o of options) {
            const opt = document.createElement('option');
            opt.value = valueFn ? valueFn(o) : o;
            opt.textContent = o;
            sel.appendChild(opt);
        }
    }

    // /update_character_data unpacks the payload POSITIONALLY (spheres_of_power is popped by
    // name), so this key order must stay exactly in sync with the Foundry module's button.js,
    // with use_backstory_api + backstory_focus appended as the optional 20th/21st inputs.
    function buildPayload(form) {
        const f = (name) => form.elements[name].value;
        return {
            input: 'Y',
            region: f('region'),
            race: f('race'),
            class: f('class'),
            bab: f('bab'),
            caster_level: f('caster_level'),
            multiclass: f('multiclass'),
            alignment: f('alignment'),
            deity: f('deity'),
            gender: f('gender'),
            randomFeats: f('randomFeats'),
            inherents: f('inherents'),
            modded_char_sheet: f('modded_char_sheet'),
            homebrew_feat_amount: f('homebrew_feat_amount'),
            spheres_of_power: f('spheres_of_power'),
            diceRolls: f('diceRolls'),
            diceSides: f('diceSides'),
            highestLevel: f('highestLevel'),
            lowestLevel: f('lowestLevel'),
            goldAmount: f('goldAmount'),
            use_backstory_api: f('use_backstory_api'),
            backstory_focus: f('backstory_focus'),
        };
    }

    async function generate(form) {
        const status = document.getElementById('gen-status');
        const btn = document.getElementById('gen-submit');
        const payload = buildPayload(form);
        localStorage.setItem(FORM_KEY, JSON.stringify(payload));
        btn.disabled = true;
        status.textContent = 'Generating… (the backend can take up to a minute)';
        try {
            const resp = await fetch('/update_character_data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            localStorage.setItem(CHAR_KEY, JSON.stringify(data));
            renderSheet(data);
            status.textContent = '';
            document.getElementById('gen-panel').classList.add('hidden');
        } catch (err) {
            status.textContent = 'Failed: ' + err.message;
        } finally {
            btn.disabled = false;
        }
    }

    function loadJsonText(text) {
        try {
            const data = JSON.parse(text);
            localStorage.setItem(CHAR_KEY, JSON.stringify(data));
            renderSheet(data);
            document.getElementById('load-panel').classList.add('hidden');
        } catch (err) {
            alert('Not valid JSON: ' + err.message);
        }
    }

    // ---------------------------------------------------------------- wiring
    document.addEventListener('DOMContentLoaded', () => {
        const form = document.getElementById('gen-form');
        fillSelect(form.elements.region, REGIONS, (r) => REGION_VALUES[r] ?? r);
        fillSelect(form.elements.race, RACES, (r) => r.toLowerCase().replace(/\s/g, '-'));
        fillSelect(form.elements.class, CLASSES, (c) => c.toLowerCase().replace(/\s/g, '-'));
        fillSelect(form.elements.deity, DEITIES);

        const savedForm = JSON.parse(localStorage.getItem(FORM_KEY) || 'null');
        if (savedForm) {
            for (const [k, v] of Object.entries(savedForm)) {
                // Disabled controls (e.g. multiclass, locked to No) keep their default;
                // a stale saved value may no longer be a valid option.
                if (form.elements[k] && !form.elements[k].disabled) form.elements[k].value = v;
            }
        }

        const toggle = (id) => document.getElementById(id).classList.toggle('hidden');
        document.getElementById('toggle-gen').addEventListener('click', () => toggle('gen-panel'));
        document.getElementById('toggle-load').addEventListener('click', () => toggle('load-panel'));
        document.getElementById('print-btn').addEventListener('click', () => window.print());
        form.addEventListener('submit', (e) => { e.preventDefault(); generate(form); });
        document.getElementById('render-paste').addEventListener('click', () =>
            loadJsonText(document.getElementById('json-paste').value));
        document.getElementById('json-file').addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) file.text().then(loadJsonText);
        });

        const saved = localStorage.getItem(CHAR_KEY);
        if (saved) {
            try { renderSheet(JSON.parse(saved)); } catch { /* stale/corrupt — leave placeholder */ }
        }
    });
})();
