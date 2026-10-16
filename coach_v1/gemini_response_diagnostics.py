"""Safe staged diagnostics around the unchanged complete-output parser.

Never returns generated text, thought text/signatures, response IDs or arbitrary
provider strings. This report diagnoses a gate; it cannot approve source facts.
"""
from .expert_collector import _json, _generated_text

FINISH={'STOP','MAX_TOKENS','SAFETY','RECITATION','LANGUAGE','OTHER','BLOCKLIST','PROHIBITED_CONTENT','SPII','MALFORMED_FUNCTION_CALL','FINISH_REASON_UNSPECIFIED'}
BLOCK={'SAFETY','OTHER','BLOCKLIST','PROHIBITED_CONTENT','IMAGE_SAFETY','BLOCK_REASON_UNSPECIFIED'}
USAGE=('promptTokenCount','cachedContentTokenCount','candidatesTokenCount','toolUsePromptTokenCount','thoughtsTokenCount','totalTokenCount')
KINDS=('text','inlineData','fileData','functionCall','functionResponse','executableCode','codeExecutionResult')

def _type(v):
 return 'null' if v is None else 'boolean' if type(v) is bool else 'integer' if type(v) is int else 'number' if type(v) is float else 'string' if isinstance(v,str) else 'array' if isinstance(v,list) else 'object' if isinstance(v,dict) else 'bytes' if isinstance(v,bytes) else 'unsupported'

def _enum(v,values):return v if isinstance(v,str) and v in values else 'MISSING' if v is None else 'UNKNOWN'

class _Check(ValueError):pass

def _check(v,code):
 if not v:raise _Check(code)

def inspect_response(raw):
 d=dict(schema_version='gemini.safe-response-diagnostics.v1',transport='HTTP200',body_kind=_type(raw),body_bytes=len(raw) if isinstance(raw,(bytes,str)) else None,
  pipeline=dict(response_body_extraction='NOT_REACHED',json_parse='NOT_REACHED',schema_validation='NOT_REACHED',text_extraction='NOT_REACHED',content_review='NOT_REACHED'),
  failed_check=None,complete_text=False,candidate_count=None,content_types=[],parts_types=[],part_kind_counts={k:0 for k in KINDS},unknown_part_key_count=0,parts_count=[],invalid_utf8_parts=0,observed_nonthought_text_bytes=0,parts_inspection_truncated=False,thought_true_parts=0,thought_false_parts=0,thought_unmarked_parts=0,thought_invalid_parts=0,signature_parts=0,finish_reasons=[],block_reason='MISSING',safety_blocked_n=0,nonthought_text_bytes=None,usage={k:None for k in USAGE},usage_available=False)
 try:
  _check(isinstance(raw,(dict,str,bytes)) and bool(raw),'NONEMPTY_RESPONSE_BODY');d['pipeline']['response_body_extraction']='PASS'
  try:r=raw if isinstance(raw,dict) else _json(raw)
  except (ValueError,TypeError,UnicodeError,RecursionError):
   d['pipeline']['json_parse']='FAIL';raise _Check('RESPONSE_JSON_PARSE') from None
  d['pipeline']['json_parse']='PASS';d['root_type']=_type(r);_check(isinstance(r,dict),'RESPONSE_OBJECT')
  usage=r.get('usageMetadata');d['usage_available']=isinstance(usage,dict)
  if isinstance(usage,dict):d['usage']={k:usage.get(k) if type(usage.get(k)) is int and 0<=usage[k]<=10**12 else None for k in USAGE}
  candidates=r.get('candidates');d['candidate_count']=len(candidates) if isinstance(candidates,list) else None
  feedback=r.get('promptFeedback');d['block_reason']=_enum(feedback.get('blockReason') if isinstance(feedback,dict) else None,BLOCK)
  if isinstance(candidates,list):
   for c in candidates[:10]:
    if not isinstance(c,dict):continue
    d['finish_reasons'].append(_enum(c.get('finishReason'),FINISH));content=c.get('content');d['content_types'].append(_type(content))
    ratings=c.get('safetyRatings');d['safety_blocked_n']+=sum(isinstance(x,dict) and x.get('blocked') is True for x in ratings) if isinstance(ratings,list) else 0
    parts=content.get('parts') if isinstance(content,dict) else None;d['parts_types'].append(_type(parts))
    if isinstance(parts,list):
     d['parts_count'].append(len(parts));d['parts_inspection_truncated']|=len(parts)>100
     for p in parts[:100]:
      if not isinstance(p,dict):continue
      for k in KINDS:d['part_kind_counts'][k]+=k in p
      d['unknown_part_key_count']+=len(set(p)-set(KINDS)-{'thought','thoughtSignature'})
      thought=p.get('thought');key='thought_unmarked_parts' if 'thought' not in p else 'thought_true_parts' if thought is True else 'thought_false_parts' if thought is False else 'thought_invalid_parts';d[key]+=1
      d['signature_parts']+='thoughtSignature' in p
      if isinstance(p.get('text'),str) and p.get('thought',False) is False:
       try:
        length=len(p['text'].encode())
        if d['observed_nonthought_text_bytes'] is not None:d['observed_nonthought_text_bytes']+=length
       except UnicodeError:d['invalid_utf8_parts']+=1;d['observed_nonthought_text_bytes']=None
  _check(isinstance(candidates,list) and len(candidates)==1,'SINGLE_CANDIDATE')
  _check(feedback is None or isinstance(feedback,dict) and not feedback.get('blockReason'),'PROMPT_NOT_BLOCKED')
  c=candidates[0];_check(isinstance(c,dict) and c.get('finishReason')=='STOP','FINISH_REASON_STOP')
  ratings=c.get('safetyRatings',[]);_check(isinstance(ratings,list) and all(isinstance(x,dict) and x.get('blocked',False) is False for x in ratings),'SAFETY_NOT_BLOCKED')
  content=c.get('content');_check(isinstance(content,dict) and content.get('role','model')=='model','MODEL_CONTENT')
  parts=content.get('parts');_check(isinstance(parts,list) and bool(parts),'NONEMPTY_PARTS')
  for p in parts:
   _check(isinstance(p,dict) and 'text' in p and set(p)<={'text','thought','thoughtSignature'},'TEXT_PART_KEYS')
   _check(isinstance(p['text'],str) and type(p.get('thought',False)) is bool,'TEXT_PART_TYPES')
   _check('thoughtSignature' not in p or isinstance(p['thoughtSignature'],str),'SIGNATURE_TYPE')
  _check(d['invalid_utf8_parts']==0,'TEXT_UTF8')
  d['pipeline']['schema_validation']='PASS'
  try:text=_generated_text(r)
  except (ValueError,TypeError,KeyError,UnicodeError):raise _Check('COMPLETE_NONEMPTY_TEXT') from None
  d['pipeline']['text_extraction']='PASS';d['nonthought_text_bytes']=len(text.encode());d['complete_text']=True
  d['probe_answer_matches_ok']=text.strip()=='OK';d['pipeline']['content_review']='TEXT_PROBE_ONLY_NOT_FACT_REVIEW'
 except _Check as e:
  d['failed_check']=str(e)
  if d['pipeline']['json_parse']=='PASS' and d['pipeline']['schema_validation']=='NOT_REACHED':d['pipeline']['schema_validation']='FAIL'
  if d['pipeline']['schema_validation']=='PASS':d['pipeline']['text_extraction']='FAIL'
 return d
