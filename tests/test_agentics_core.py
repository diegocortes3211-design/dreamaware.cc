from services.agentics.executive import Executive, Action
from services.agentics.evaluator import Evaluator
from services.agentics.self_modify import SelfModifier


def test_scaffold_exists():
    e = Executive()
    actions = e.plan("test objective")
    assert any(isinstance(a, Action) for a in actions)
    run_out = e.run(actions)
    assert "actions" in run_out

    ev = Evaluator()
    summary = ev.evaluate(run_out)
    assert "score" in summary

    sm = SelfModifier()
    props = sm.propose(summary)
    assert isinstance(props, list)