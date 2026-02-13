from decimal import Decimal
from app.services.rail_selector import select_rail


def test_small_amount_selects_fednow():
    rail = select_rail(Decimal("1000"), "fednow,rtp,ach,card")
    assert rail == "fednow"


def test_over_fednow_selects_rtp():
    rail = select_rail(Decimal("600000"), "fednow,rtp,ach,card")
    assert rail == "rtp"


def test_over_rtp_selects_ach():
    rail = select_rail(Decimal("1500000"), "fednow,rtp,ach,card")
    assert rail == "ach"


def test_preferred_rail_respected():
    rail = select_rail(Decimal("1000"), "fednow,rtp,ach,card", preferred_rail="rtp")
    assert rail == "rtp"


def test_preferred_rail_over_limit_falls_back():
    rail = select_rail(Decimal("600000"), "fednow,rtp,ach,card", preferred_rail="fednow")
    assert rail == "rtp"


def test_no_suitable_rail():
    rail = select_rail(Decimal("20000000"), "fednow,rtp")
    assert rail is None


def test_limited_rails():
    rail = select_rail(Decimal("1000"), "ach,card")
    assert rail == "ach"


def test_card_only():
    rail = select_rail(Decimal("100"), "card")
    assert rail == "card"


def test_card_over_limit():
    rail = select_rail(Decimal("60000"), "card")
    assert rail is None
