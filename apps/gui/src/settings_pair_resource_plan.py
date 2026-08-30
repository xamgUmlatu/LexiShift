from __future__ import annotations

from dataclasses import dataclass

from i18n import t
from lexishift_core.helper.source_stacks import (
    available_source_stacks,
    normalize_pair_key,
    source_stack_for_pair,
)


@dataclass(frozen=True)
class PairResourceItem:
    pair: str
    kind: str
    pack_id: str
    label_key: str
    optional: bool = False
    available: bool = True

    @property
    def label(self) -> str:
        return t(self.label_key)


@dataclass(frozen=True)
class PairResourcePlan:
    pair: str
    label_key: str
    resources: tuple[PairResourceItem, ...]

    @property
    def label(self) -> str:
        return t(self.label_key)

    @property
    def required_resources(self) -> tuple[PairResourceItem, ...]:
        return tuple(resource for resource in self.resources if not resource.optional)


def _plan_from_source_stack(pair: str | None) -> PairResourcePlan | None:
    stack = source_stack_for_pair(pair)
    if stack is None:
        return None
    resources = tuple(
        PairResourceItem(
            pair=stack.pair,
            kind=resource.family,
            pack_id=resource.pack_id,
            label_key=resource.label_key,
            optional=bool(resource.optional_for and not resource.required_for),
            available=resource.wired,
        )
        for resource in stack.pair_setup_resources()
    )
    if not resources:
        return None
    return PairResourcePlan(
        pair=stack.pair,
        label_key=stack.label_key,
        resources=resources,
    )


def pair_resource_plan(pair: str | None) -> PairResourcePlan | None:
    return _plan_from_source_stack(normalize_pair_key(pair))


def available_pair_resource_plans() -> tuple[PairResourcePlan, ...]:
    plans = (_plan_from_source_stack(stack.pair) for stack in available_source_stacks())
    return tuple(plan for plan in plans if plan is not None)
