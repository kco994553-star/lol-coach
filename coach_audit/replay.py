"""Separate player reference and truth archive; evaluation gates are not coaching scores."""
ERROR_CLASSES = ('STATE_ERROR', 'KNOWLEDGE_ERROR', 'STRATEGY_ERROR', 'DECISION_ERROR',
                 'EXECUTION_ERROR', 'COACH_ERROR', 'EXTRACTION_ERROR', 'EVIDENCE_GAP')
EVALUATION_ORDER = ('state', 'knowledge', 'strategy', 'decision', 'execution', 'coach', 'outcome')


def compare_reference_values(reference, extracted):
    """Diagnostic equality only, never reference authentication or accuracy evidence."""
    import json
    def same(a, b):
        return json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(b, sort_keys=True, allow_nan=False)
    mismatches = [key for key, value in reference.items()
                  if key not in extracted or not same(extracted[key], value)]
    return dict(scope='DECLARED_REFERENCE_ONLY', fields_compared=len(reference),
                values_equal=len(reference)-len(mismatches), mismatches=mismatches,
                classification_candidate='STATE_ERROR' if mismatches else None)


def compare_player_state(case, extracted_player_state):
    ref = case['reference']['PLAYER_INFORMATION_STATE']
    ready = ref['status'] == 'ESTABLISHED' and bool(ref['evidence_refs']) and bool(ref['fields'])
    # A caller-supplied ESTABLISHED label/string source reference cannot authenticate
    # a real player view, time, patch or independently reviewed source. R7 has no
    # verified replay reference importer. A useful local comparison remains separate.
    return dict(status='BLOCKED', classification='EVIDENCE_GAP', denominator=0, matches=0,
                mismatches=[], engine_eligible=False,
                reason='REFERENCE_PROVENANCE_UNVERIFIED' if ready else 'PLAYER_REFERENCE_NOT_ESTABLISHED',
                diagnostic=compare_reference_values(ref['fields'], extracted_player_state) if ready else None)


def evaluate_ordered(stages):
    """Outcome cannot override earlier failure or missing evidence."""
    for stage in EVALUATION_ORDER:
        status = stages.get(stage, 'NOT_RUN')
        if status not in ('PASS', 'FAIL', 'NOT_RUN'):
            raise ValueError('INVALID_STAGE_STATUS')
        if status != 'PASS':
            classification = {'state':'STATE_ERROR', 'knowledge':'KNOWLEDGE_ERROR', 'strategy':'STRATEGY_ERROR',
                              'decision':'DECISION_ERROR', 'execution':'EXECUTION_ERROR', 'coach':'COACH_ERROR'}.get(stage)
            return dict(first_unresolved_stage=stage,
                        classification='EVIDENCE_GAP' if status == 'NOT_RUN' else classification,
                        decision_quality=stages.get('decision', 'NOT_RUN') if EVALUATION_ORDER.index(stage) >= 3 else 'NOT_EVALUATED',
                        outcome_used_for_decision=False)
    return dict(first_unresolved_stage=None, classification=None, decision_quality='PASS', outcome_used_for_decision=False)
