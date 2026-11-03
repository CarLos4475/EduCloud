from campus.config import institutional_email


def test_exact_university_domain_only():
    assert institutional_email("pilot@pcpuma.acatlan.unam.mx")
    assert institutional_email("PILOT@PCPUMA.ACATLAN.UNAM.MX")
    assert not institutional_email("pilot@pcpuma.acatlan.unam.mx.evil.test")
    assert not institutional_email("pilot@evil.pcpuma.acatlan.unam.mx")
    assert not institutional_email("pilot@example.test")
    assert not institutional_email("@pcpuma.acatlan.unam.mx")
    assert not institutional_email("pilot@another@pcpuma.acatlan.unam.mx")
