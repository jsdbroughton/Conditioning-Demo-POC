"""Offline tests for the non-wall category engine (conditioning/categories.py).

The thing these pin is the PRINCIPLE, not the table: no single field decides
a code on its own. Category, Function, type name, an existing Assembly Code
and a coded neighbour are independent signals that corroborate or contradict
each other through the same constants the wall engine uses — so the tests
below are mostly about what happens when they agree, disagree, or are
missing, with the specific codes only as the vehicle.
"""

from __future__ import annotations

from conditioning.categories import (
    CATEGORY_RULES,
    classify_categories,
    classify_element,
    read_element,
)
from conditioning.codes import (
    ACME_CODES,
    CONFLICT_PENALTY,
    CORROBORATION_CAP,
    METHOD_CONFIDENCE,
)
from tests.fakes import FakeModel, FakeModelObject

_TYPE = "Parameters.Type Parameters."


def _obj(app_id: str, category: str, host=None, parent=None, **params):
    props = {"category": category}
    for key, value in params.items():
        props[{
            "type": "type",
            "family": "family",
            "function": f"{_TYPE}Construction.Function",
            "assembly_code": f"{_TYPE}Identity Data.Assembly Code",
            "type_mark": f"{_TYPE}Identity Data.Type Mark",
        }[key]] = value
    return FakeModelObject(
        application_id=app_id, properties=props, host=host, parent=parent
    )


def _classify(obj, references=()):
    element = read_element(obj)
    refs = [read_element(r) for r in references]
    return classify_element(element, refs)


class TestEveryRuleCodeIsReal:
    """The table can only hand out codes the client actually has."""

    def test_every_code_in_the_table_exists_in_the_reference(self):
        """No rule points at a code the spreadsheet doesn't contain."""
        codes = set()
        for rule in CATEGORY_RULES.values():
            if rule.default:
                codes.add(rule.default)
            codes.update(rule.by_function.values())
            codes.update(code for _, code in rule.by_keyword)
        missing = sorted(c for c in codes if c not in ACME_CODES)
        assert not missing, missing


class TestNoSingleFieldDecides:
    """Category, Function, name, legacy code — each is a signal, none is a verdict."""

    def test_category_alone_places_an_unambiguous_category_at_tier_1(self):
        """Stairs → B1080.10 from category alone; Revit's category is a fact."""
        result = _classify(_obj("s1", "Stairs", type="Monolithic Stair"))
        assert (result.code, result.method, result.tier) == (
            "B1080.10", "heuristic_category", 1
        )
        assert result.confidence == METHOD_CONFIDENCE["heuristic_category"]

    def test_category_alone_cannot_place_a_door(self):
        """Doors has no default: no Function, no keyword → not codable at all."""
        assert _classify(_obj("d1", "Doors", type="Single Flush")) is None

    def test_function_chooses_the_section_for_a_door(self):
        """Exterior → B2050 section; interior → C1030 section."""
        ext = _classify(_obj("d1", "Doors", function="Exterior"))
        inte = _classify(_obj("d2", "Doors", function="Interior"))
        assert ext.code == "B2050.10"
        assert inte.code == "C1030.10"
        assert ext.method == "heuristic_function"

    def test_agreeing_keyword_refines_within_the_section_and_corroborates(self):
        """Exterior + 'overhead' → B2050.30, confidence lifted for agreement."""
        result = _classify(
            _obj("d1", "Doors", function="Exterior", type="Overhead Sectional")
        )
        assert result.code == "B2050.30"
        assert result.confidence == min(
            CORROBORATION_CAP, METHOD_CONFIDENCE["heuristic_function"] + 0.10
        )
        assert "corroborated by" in result.basis

    def test_conflicting_keyword_costs_confidence_and_does_not_cross_sections(self):
        """Exterior + 'sliding' (an interior code) → stays B2050.10, penalised."""
        result = _classify(
            _obj("d1", "Doors", function="Exterior", type="Sliding Glass")
        )
        assert result.code == "B2050.10"
        assert result.confidence == round(
            METHOD_CONFIDENCE["heuristic_function"] - CONFLICT_PENALTY, 3
        )
        assert "contradicted by" in result.basis
        assert result.tier == 2

    def test_keyword_alone_is_tier_3(self):
        """A door with only a name to go on is a low-confidence guess, and says so."""
        result = _classify(_obj("d1", "Doors", type="Coiling Fire Shutter"))
        assert result.code == "C1030.40"
        assert result.method == "heuristic_name"
        assert result.tier == 3

    def test_legacy_code_section_corroborates_a_category_default(self):
        """A legacy 7-digit code in the same section lifts confidence."""
        plain = _classify(_obj("f1", "Floors", type="Concrete 8in"))
        legacy = _classify(
            _obj("f2", "Floors", type="Concrete 8in", assembly_code="B1010200")
        )
        assert plain.code == legacy.code == "B1010.20"
        assert legacy.confidence > plain.confidence
        assert legacy.original_code == "B1010200"

    def test_legacy_code_in_a_different_section_is_a_conflict(self):
        """Floors default B1010 vs a legacy A4010 code → penalised, code unchanged."""
        result = _classify(
            _obj("f1", "Floors", type="Concrete 8in", assembly_code="A4010100")
        )
        assert result.code == "B1010.20"
        assert result.confidence < CATEGORY_RULES["Floors"].default_confidence
        assert "contradicted by" in result.basis

    def test_type_mark_never_decides_a_code(self):
        """Type Mark is a fingerprint field for similarity, not a signal."""
        with_mark = _classify(_obj("d1", "Doors", type_mark="D1"))
        assert with_mark is None


class TestExistingAndSimilarity:
    """Already-coded objects pass through; coded neighbours vouch for their kind."""

    def test_existing_valid_code_passes_through_at_tier_0(self):
        """A door already carrying C1030.10 is 'existing', untouched."""
        result = _classify(_obj("d1", "Doors", assembly_code="C1030.10"))
        assert (result.method, result.tier, result.code) == ("existing", 0, "C1030.10")

    def test_a_code_from_the_reference_but_wrong_shape_is_not_existing(self):
        """Level 3 'C1030' is in the reference but isn't a Level 4 code."""
        result = _classify(
            _obj("d1", "Doors", assembly_code="C1030", function="Interior")
        )
        assert result.method != "existing"
        assert result.original_code == "C1030"

    def test_similarity_to_a_coded_neighbour_of_the_same_category_wins(self):
        """A near-identical coded door decides before any heuristic does."""
        ref = _obj("d0", "Doors", type="Single Flush 36x84 HM", family="Door-Single",
                   assembly_code="C1030.20")
        target = _obj("d1", "Doors", type="Single Flush 36x84 HM", family="Door-Single",
                      function="Exterior")  # Function would have said B2050
        result = _classify(target, references=[ref])
        assert result.method == "similarity"
        assert result.code == "C1030.20"
        assert result.matched_from == "Single Flush 36x84 HM"

    def test_similarity_below_threshold_falls_through_to_signals(self):
        """A distant coded neighbour is not reached past — nearest or nothing."""
        ref = _obj("d0", "Doors", type="Revolving Entrance", assembly_code="B2050.10")
        target = _obj("d1", "Doors", type="Single Flush", function="Interior")
        result = _classify(target, references=[ref])
        assert result.method == "heuristic_function"
        assert result.code == "C1030.10"


class TestClassifyCategories:
    """Whole-model behaviour: scope, exclusion, silence where unsure."""

    def test_walls_are_excluded_and_unknown_categories_ignored(self):
        """Walls have their own engine; Rooms have no rule; both stay out."""
        wall = _obj("w1", "Walls", type="Basic Wall")
        room = _obj("r1", "Rooms", type="Room")
        stair = _obj("s1", "Stairs", type="Stair")
        results = classify_categories(
            FakeModel([wall, room, stair]), exclude_ids={"w1"}
        )
        assert [r.object_id for r in results] == ["s1"]

    def test_reference_pool_is_per_category(self):
        """A coded Window can't vouch for a Door with the same type name."""
        window = _obj("w1", "Windows", type="Fixed 36x84", assembly_code="B2020.20")
        door = _obj("d1", "Doors", type="Fixed 36x84")
        results = classify_categories(FakeModel([window, door]), exclude_ids=set())
        by_id = {r.object_id: r for r in results}
        assert by_id["w1"].method == "existing"
        assert "d1" not in by_id  # nothing else could place it

    def test_unrecognised_mechanical_equipment_stays_unplaced(self):
        """A generic equipment name with no code signal is not guessed."""
        obj = _obj("m1", "Mechanical Equipment", type="Widget 3000")
        assert _classify(obj) is None
        named = _classify(_obj("m2", "Mechanical Equipment", type="AHU-1 Air Handler"))
        assert named.code == "D3050.50"


class TestRelationsAsSignals:
    """The wall a door sits in, and the element a part belongs to, are evidence too."""

    def test_host_wall_function_places_a_door_with_no_function_of_its_own(self):
        """2,563 live doors had no Function; the exterior wall they sit in does."""
        wall = _obj("w1", "Walls", function="Exterior")
        door = _obj("d1", "Doors", type="Single Flush", host=wall)
        result = _classify(door)
        assert result.code == "B2050.10"
        assert result.method == "heuristic_host_function"
        assert result.tier == 2  # weaker than the door's own Function
        assert "host wall (Exterior)" in result.basis

    def test_own_function_outranks_host_function_and_they_can_conflict(self):
        """Interior vestibule door in an exterior wall: door wins, confidence drops."""
        wall = _obj("w1", "Walls", function="Exterior")
        door = _obj("d1", "Doors", function="Interior", host=wall)
        result = _classify(door)
        assert result.code == "C1030.10"
        assert result.method == "heuristic_function"
        assert "contradicted by" in result.basis

    def test_agreeing_host_and_own_function_corroborate(self):
        """Both say exterior → confidence lifted."""
        wall = _obj("w1", "Walls", function="Exterior")
        door = _obj("d1", "Doors", function="Exterior", host=wall)
        result = _classify(door)
        assert result.code == "B2050.10"
        assert result.confidence > METHOD_CONFIDENCE["heuristic_function"]

    def test_sub_elements_inherit_a_placed_parent(self):
        """Railing supports/handrails take the railing's code, tier and all."""
        railing = _obj("r1", "Railings", type="Guardrail Pipe")
        support = _obj("s1", "Supports", parent=railing)
        handrail = _obj("h1", "Handrails", type="Circular", parent=railing)
        results = classify_categories(
            FakeModel([railing, support, handrail]), exclude_ids=set()
        )
        by_id = {r.object_id: r for r in results}
        assert by_id["r1"].code == "B1080.50"
        for child in ("s1", "h1"):
            assert by_id[child].code == "B1080.50"
            assert by_id[child].method == "heuristic_parent"
            assert by_id[child].tier == by_id["r1"].tier
            assert "parent element (Railings)" in by_id[child].basis

    def test_child_of_an_unplaced_parent_stays_unplaced(self):
        """Inheritance carries a real result, never a blank."""
        gm = _obj("g1", "Generic Models", type="Thing")
        part = _obj("p1", "Supports", parent=gm)
        results = classify_categories(FakeModel([gm, part]), exclude_ids=set())
        assert results == []
