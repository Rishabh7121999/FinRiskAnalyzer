from app.models.state import merge_dict, merge_list


def test_merge_dict_combines_disjoint_keys():
    existing = {"AAA.NS": {"score": 1}}
    new = {"BBB.NS": {"score": 2}}

    result = merge_dict(existing, new)

    assert result == {"AAA.NS": {"score": 1}, "BBB.NS": {"score": 2}}


def test_merge_dict_new_value_wins_on_key_collision():
    existing = {"AAA.NS": {"score": 1}}
    new = {"AAA.NS": {"score": 2}}

    result = merge_dict(existing, new)

    assert result == {"AAA.NS": {"score": 2}}


def test_merge_dict_does_not_mutate_inputs():
    existing = {"AAA.NS": {"score": 1}}
    new = {"BBB.NS": {"score": 2}}

    merge_dict(existing, new)

    assert existing == {"AAA.NS": {"score": 1}}
    assert new == {"BBB.NS": {"score": 2}}


def test_merge_list_concatenates_in_order():
    existing = ["financial_analysis"]
    new = ["news_analysis"]

    result = merge_list(existing, new)

    assert result == ["financial_analysis", "news_analysis"]


def test_merge_list_does_not_mutate_inputs():
    existing = ["financial_analysis"]
    new = ["news_analysis"]

    merge_list(existing, new)

    assert existing == ["financial_analysis"]
    assert new == ["news_analysis"]
