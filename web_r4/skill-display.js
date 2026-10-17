/* Pure display adapter. Stored/source text and tactical reports are never mutated. */
(function (root) {
  'use strict';
  const data = typeof module === 'object' && module.exports ? require('./skill-data.js') : root.LoLSkillNames;
  const roster = data && data.champions || {};
  const slots = new Set(['P', 'Q', 'W', 'E', 'R']);
  const escape = text => String(text).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const all = Object.values(roster);
  const aliases = new Map(all.flatMap(champion => [[champion.id.toLocaleLowerCase(), champion.id], [champion.name, champion.id]]));
  const resolve = value => typeof value === 'string' ? aliases.get(value.toLocaleLowerCase()) || null : null;
  const champion = value => roster[resolve(value)] || null;

  function label(owner, slot) {
    const who = champion(owner);
    return who && slots.has(slot) && who.slots[slot] ? who.name + '의 ' + who.slots[slot].trim() + '(' + slot + ')' : null;
  }

  function slotFromFact(owner, fact) {
    const who = champion(owner);
    if (!who || !fact || fact.slot === 'ITEM' || fact.spell_kind === 'SUMMONER') return null;
    const explicit = slots.has(fact.slot) ? fact.slot : null;
    const locator = fact.locator || fact.source && fact.source.locator;
    if (locator) {
      const match = String(locator).match(/^data\.([A-Za-z0-9]+)\.(passive|spells\.([0-3]))\.(?:name|description|tooltip)$/);
      if (!match || match[1] !== who.id) return null;
      const mapped = match[2] === 'passive' ? 'P' : 'QWER'[Number(match[3])];
      return explicit && explicit !== mapped ? null : mapped;
    }
    return explicit;
  }

  function factLabel(owner, fact) {
    const who = champion(owner), slot = slotFromFact(owner, fact);
    const name = String(fact && (fact.name || fact.ability) || '기술 미확인');
    if (fact && (fact.slot === 'ITEM' || fact.spell_kind === 'SUMMONER')) return name;
    if (who && slot && who.slots[slot].trim() === name.trim()) return label(who.id, slot);
    return (who ? who.name + '의 ' : '') + name + '(키 미확인)';
  }

  function resolveSlot(owner, name) {
    const who = champion(owner);
    if (!who || typeof name !== 'string') return null;
    const input = name.trim(), existing = input.match(/\(([PQWER])\)$/);
    const clean = input.replace(/\s*\([PQWER]\)$/, '').trim();
    const exact = Object.entries(who.slots).filter(([, text]) => text.trim() === clean);
    // Some official names themselves start with their champion (나르!, 드레이븐의 리그).
    // Match the complete official name before removing an added display owner prefix.
    const withoutOwner = clean.replace(new RegExp('^' + escape(who.name) + '(?:의\\s+|\\s+)'), '').trim();
    const found = exact.length ? exact : Object.entries(who.slots).filter(([, text]) => text.trim() === withoutOwner);
    return found.length === 1 && (!existing || existing[1] === found[0][0]) ? found[0][0] : null;
  }

  function format(value, options) {
    if (value == null) return '';
    let text = String(value);
    const opts = options || {}, tokens = [];
    const protect = rendered => { const token = '\uE000' + tokens.length + '\uE001'; tokens.push(rendered); return token; };
    // Explicit authored mention bindings disambiguate an individual display field.
    [...(opts.bindings || [])].filter(binding => binding && typeof binding.text === 'string' && binding.text)
      .sort((a, b) => b.text.length - a.text.length).forEach(binding => {
        const rendered = label(binding.champion, binding.slot);
        if (!rendered) return;
        const replacement = binding.prefix ? binding.text.replace(/^[PQWER]/, protect(rendered)) : protect(rendered);
        if (binding.prefix && !/^[PQWER]/.test(binding.text)) return;
        text = text.split(binding.text).join(replacement);
      });
    const ids = Array.isArray(opts.champions) ? opts.champions.map(resolve).filter(Boolean) : Object.keys(roster);
    const active = [...new Set([...ids, resolve(opts.owner), resolve(opts.own)].filter(Boolean))].map(id => roster[id]);
    const ownerAliases = [...new Set(active.flatMap(who => [who.name, who.id]))].sort((a, b) => b.length - a.length);
    if (ownerAliases.length) {
      const owners = ownerAliases.map(escape).join('|');
      // Explicit owner/key groups only. A bare key is never assigned to own/first pick.
      const keyPattern = new RegExp('(' + owners + '|내)\\s*(?:의\\s*)?([PQWER](?:\\s*[/·]\\s*[PQWER])*)(?:\\s*\\([PQWER]\\))*(?=$|[^A-Za-z0-9_:])', 'g');
      text = text.replace(keyPattern, (original, owner, keys) => {
        const id = owner === '내' ? resolve(opts.own) : resolve(owner);
        const rendered = keys.split(/\s*[/·]\s*/).map(key => label(id, key));
        return rendered.every(Boolean) ? protect(rendered.join(' · ')) : original;
      });
      const names = new Map();
      active.forEach(who => Object.entries(who.slots).forEach(([slot, rawName]) => {
        const name = rawName.trim();
        if (!names.has(name)) names.set(name, []);
        names.get(name).push({ champion: who.id, slot });
      }));
      const orderedNames = [...names.keys()].sort((a, b) => b.length - a.length);
      const namePattern = new RegExp('(?:(' + owners + ')\\s*(?:의\\s*)?)?(' + orderedNames.map(escape).join('|') + ')((?:\\s*\\([PQWER]\\))*)', 'g');
      text = text.replace(namePattern, (original, explicitOwner, name, keySuffix) => {
        // Ordinary prose such as 준비/반격/공포 is not an ability reference.
        // Unqualified names are allowed only in an explicitly typed skill-name field.
        let candidates = names.get(name) || [];
        const boundedAliases = (opts.aliases || []).filter(binding => {
          const who = champion(binding.champion);
          return who && who.slots[binding.slot] && who.slots[binding.slot].trim() === name && name.includes(binding.text);
        });
        if (!explicitOwner && opts.skillNames !== true && !keySuffix && !boundedAliases.length) return protect(original);
        if (!explicitOwner && keySuffix) {
          const existing = [...keySuffix.matchAll(/\(([PQWER])\)/g)].map(match => match[1]);
          candidates = candidates.filter(item => existing.every(key => key === item.slot));
        }
        if (!explicitOwner && boundedAliases.length && !keySuffix) candidates = candidates.filter(item => boundedAliases.some(binding => resolve(binding.champion) === item.champion && binding.slot === item.slot));
        const owner = resolve(explicitOwner) || resolve(opts.owner);
        if (owner) candidates = candidates.filter(item => item.champion === owner);
        // Genuine same-name collisions remain unresolved without an explicit owner.
        return candidates.length === 1 ? protect(label(candidates[0].champion, candidates[0].slot)) : original;
      });
    }
    // Canonical names are protected before bounded shorthand aliases, so `덫`
    // never replaces the substring of an already formatted `요들잡이 덫(W)`.
    [...(opts.aliases || [])].filter(binding => binding && typeof binding.text === 'string' && binding.text)
      .sort((a, b) => b.text.length - a.text.length).forEach(binding => {
        const rendered = label(binding.champion, binding.slot);
        if (rendered) text = text.split(binding.text).join(protect(rendered));
      });
    return text.replace(/\uE000(\d+)\uE001/g, (_, index) => tokens[Number(index)]);
  }

  const api = Object.freeze({ format, label, factLabel, slotFromFact, resolveSlot, resolve, source_patch: data && data.source_patch });
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.SkillDisplay = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
