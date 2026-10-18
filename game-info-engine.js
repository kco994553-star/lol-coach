/* One held-inventory valuation rule; never a combat strength or win model. */
(function(root,factory){if(typeof module==='object'&&module.exports)module.exports=factory();else root.GameInfo=factory();})(typeof globalThis!=='undefined'?globalThis:this,function(){
 'use strict';
 function value(inventory,catalog,patch){
  if(!Array.isArray(inventory)||inventory.length>7)throw Error('보유 슬롯 목록을 확인해 주세요.');
  const ids=new Set(),missing=[],rows=[];let subtotal=0;
  const match=typeof patch==='string'&&/^\d+\.\d+(?:\.\d+){0,2}$/.test(patch)&&patch.split('.').slice(0,2).join('.')===catalog.patch;
  for(const item of inventory){
   if(!item||!Number.isInteger(item.slot)||item.slot<0||item.slot>6||ids.has(item.slot)||!Number.isInteger(item.count)||item.count<1||item.count>100)throw Error('슬롯 중복 또는 수량 오류입니다.');
   ids.add(item.slot);const fact=catalog.items[String(item.id)],ok=match&&fact&&Number.isInteger(fact.total)&&fact.total>=0;
   if(!ok)missing.push({slot:item.slot,reason:!match?'PATCH_UNKNOWN_OR_MISMATCH':'ITEM_PRICE_UNKNOWN'});
   const amount=ok?fact.total*item.count:null;if(ok)subtotal+=amount;
   rows.push({slot:item.slot,id:String(item.id),count:item.count,name:fact?.name||'가격 미확인',value:amount});
  }
  return{format:'lol-coach-item-value-v1',kind:'MANUAL_HYPOTHESIS',patch,source:catalog.source,rows,total:match&&!missing.length?subtotal:null,known_subtotal:match?subtotal:null,missing,cash:null,earned_gold:null,price_basis:'HELD_SLOTS_CATALOG_TOTAL_NOT_SPENT_GOLD',combat_advantage:null};
 }
 function compare(ours,theirs,catalog,patch){const a=value(ours,catalog,patch),b=value(theirs,catalog,patch);return{ours:a,theirs:b,difference:a.total===null||b.total===null?null:a.total-b.total};}
 function participantValue(inventory,catalog,patch){
  try{return value(inventory,catalog,patch);}catch(_){
   if(!Array.isArray(inventory)||inventory.length>7)return{total:null,known_subtotal:null,missing:[{reason:'INVENTORY_SCHEMA'}]};
   const slots=new Map();for(const row of inventory)if(row&&Number.isInteger(row.slot))slots.set(row.slot,(slots.get(row.slot)||0)+1);
   const valid=inventory.filter(row=>row&&Number.isInteger(row.slot)&&row.slot>=0&&row.slot<=6&&slots.get(row.slot)===1&&Number.isInteger(row.count)&&row.count>=1&&row.count<=100);
   const partial=value(valid,catalog,patch);return{...partial,total:null,known_subtotal:valid.length?partial.known_subtotal:null,missing:[...partial.missing,{reason:'INVENTORY_SCHEMA',omitted:inventory.length-valid.length}]};
  }
 }
 function teams(players,catalog,patch){
  if(!Array.isArray(players)||players.length>10)throw Error('참가자 목록을 확인해 주세요.');
  const out={};for(const side of ['ORDER','CHAOS']){const group=players.filter(p=>p&&p.team===side),values=group.map(p=>participantValue(p.items,catalog,patch)),known=values.filter(v=>v.known_subtotal!==null);out[side]={observed_players:group.length,expected_players:5,total:group.length===5&&values.every(v=>v.total!==null)?values.reduce((n,v)=>n+v.total,0):null,known_subtotal:known.length?known.reduce((n,v)=>n+v.known_subtotal,0):null,inventory_omissions:values.reduce((n,v)=>n+(v.missing?.length||0),0)};}
  out.difference=out.ORDER.total===null||out.CHAOS.total===null?null:out.ORDER.total-out.CHAOS.total;return out;
 }

 return Object.freeze({value,compare,teams});
});
