# Obligations of the pay tool: the comparison and the access check are code, so they're tested
# here, with no model. (Whether the model calls the tool when it should is a tendency: see evals/.)
import pay_tool

EMPLOYEES = pay_tool.load_employees()  # the made-up comp_ranges.csv


def test_below_band():
    # Marcus: $61,000 against a $64,000 minimum, the case the model got wrong with --raw
    record = pay_tool.get_pay_range(EMPLOYEES["Marcus Brown"])
    assert (record["status"], record["by"]) == ("below band", 3000)


def test_within_band():
    # Jordan: $78,000 in a $72,000–92,000 band
    assert pay_tool.get_pay_range(EMPLOYEES["Jordan Lee"])["status"] == "within band"


def test_only_their_manager_may_see():
    # Sam manages Marcus; Jordan doesn't, so the tool refuses before the model sees anything
    assert pay_tool.may_see("Sam Okafor", EMPLOYEES["Marcus Brown"])
    assert not pay_tool.may_see("Jordan Lee", EMPLOYEES["Marcus Brown"])
