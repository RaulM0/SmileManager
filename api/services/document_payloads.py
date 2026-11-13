def notice_payload(notice):
    return {'clinic': str(notice.clinic_id), 'version': notice.version, 'body': notice.body,
            'approved_by': notice.approved_by_id, 'approved_name': notice.approved_name, 'published_at': notice.published_at}


def template_payload(template):
    return {'clinic': str(template.clinic_id), 'kind': template.kind, 'version': template.version,
            'title': template.title, 'text': template.text, 'privacy_notice': template.privacy_notice_id,
            'approved_by': template.approved_by_id, 'approved_name': template.approved_name, 'published_at': template.published_at}


def evidence_payload(record):
    return {key: str(getattr(record, key)) for key in (
        'clinic_id', 'patient_id', 'template_id', 'template_sha256', 'supersedes_id', 'recorded_by_id', 'recorded_name', 'recorded_at',
        'signer_name', 'signer_role', 'representative_basis', 'signed_on', 'file_sha256',
    )}


def consultation_payload(consultation):
    return {key: str(getattr(consultation, key)) for key in (
        'paciente_id', 'medico_id', 'author_name', 'fecha_consulta', 'motivo_consulta',
        'diagnostico', 'tratamiento', 'observaciones', 'closed_at',
    )}


def addendum_payload(addendum):
    return {key: str(getattr(addendum, key)) for key in ('consultation_id', 'author_id', 'author_name', 'text', 'created_at', 'base_content_sha256')}


def revision_payload(revision):
    return {'clinic': str(revision.clinic_id), 'patient': revision.patient_id, 'actor': revision.actor_id,
            'actor_name': revision.actor_name, 'resource_type': revision.resource_type,
            'resource_id': revision.resource_id, 'version': revision.version, 'snapshot': revision.snapshot, 'created_at': revision.created}
