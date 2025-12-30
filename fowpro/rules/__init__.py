"""
Force of Will Comprehensive Rules Module
=========================================
Based on CR version 12.7 (Sep 18, 2025), filtered for Grimm Cluster era.

This module defines the core types, enums, and structures for implementing
FoW game mechanics according to the official comprehensive rules.

Systems Implemented:
- types.py: Core enums and type definitions (CR 901, 906, 1000+, 1100+)
- targeting.py: Target selection and validation (CR 1015)
- conditions.py: Condition checking for effects
- modals.py: Modal choice handling ("Choose one", etc.)
- effects.py: Effect definitions and builders
- abilities.py: Ability type implementations (CR 904-907)
- priority.py: Priority system (CR 604-605)
- costs.py: Cost calculation and payment (CR 402, 1002)
- layers.py: Continuous effect layer system (CR 909)
- keywords.py: Keyword ability implementations (CR 1100+)
- replacement.py: Replacement effects (CR 910)
- triggers.py: Trigger management with APNAP ordering (CR 906)
"""

from .types import (
    # Ability types (CR 901)
    AbilityType,
    EffectTiming,

    # Trigger conditions (CR 906)
    TriggerCondition,
    TriggerTiming,

    # Effect actions (CR 1000+)
    EffectAction,

    # Keywords (CR 1100+)
    KeywordAbility,

    # Duration
    EffectDuration,
)

from .targeting import (
    TargetRequirement,
    TargetFilter,
    TargetZone,
    TargetController,
    CommonFilters,
)

from .conditions import (
    Condition,
    ConditionType,
    ConditionOperator,
    ConditionBuilder,
)

from .modals import (
    ModalChoice,
    Mode,
    ModalPatterns,
)

from .effects import (
    Effect,
    EffectBuilder,
    ContinuousEffect,
    ReplacementEffect,
)

from .abilities import (
    Ability,
    ActivateAbility,
    AutomaticAbility,
    ContinuousAbility,
    WillAbility,
    JudgmentAbility,
    AbilityFactory,
    ModalAbility,
    IncarnationCost,
    AwakeningCost,
)

# New CR-compliant systems
from .priority import (
    PriorityManager,
    PendingAction,
    ActionType,
    PriorityState,
)

from .costs import (
    CostManager,
    CostType,
    WillType,
    WillCost,
    AdditionalCost,
    AlternativeCost,
    CostReduction,
    CostIncrease,
    CostPaymentPlan,
    CostBuilder,
)

from .layers import (
    LayerManager,
    Layer,
    LayeredEffect,
    LayeredEffectBuilder,
)

from .keywords import (
    KeywordManager,
    Keyword,
    KeywordHandler,
    parse_keywords_from_text,
)

from .replacement import (
    ReplacementManager,
    ReplacementEffect as ReplacementEffectCR,  # Alias to avoid conflict
    ReplacementEffectResult,
    ReplacementEventType,
    ReplacementBuilder,
)

from .triggers import (
    APNAPTriggerManager,
    TriggerInstance,
    TriggeredAbility,
    TriggerType,
    TriggerBuilder,
)

from .choices import (
    ChoiceManager,
    Choice,
    ChoiceType,
    ChoiceState,
    ChoiceUIMessage,
)

from .integration import (
    RulesEngine,
    enhance_engine,
)

__all__ = [
    # Types
    'AbilityType', 'EffectTiming', 'TriggerCondition', 'TriggerTiming',
    'EffectAction', 'KeywordAbility', 'EffectDuration',

    # Targeting
    'TargetRequirement', 'TargetFilter', 'TargetZone', 'TargetController', 'CommonFilters',

    # Conditions
    'Condition', 'ConditionType', 'ConditionOperator', 'ConditionBuilder',

    # Modals
    'ModalChoice', 'Mode', 'ModalPatterns',

    # Effects
    'Effect', 'EffectBuilder', 'ContinuousEffect', 'ReplacementEffect',

    # Abilities
    'Ability', 'ActivateAbility', 'AutomaticAbility', 'ContinuousAbility', 'WillAbility',
    'AbilityFactory',

    # Priority System (CR 604-605)
    'PriorityManager', 'PendingAction', 'ActionType', 'PriorityState',

    # Cost System (CR 402, 1002)
    'CostManager', 'CostType', 'WillType', 'WillCost', 'AdditionalCost',
    'AlternativeCost', 'CostReduction', 'CostIncrease', 'CostPaymentPlan', 'CostBuilder',

    # Layer System (CR 909)
    'LayerManager', 'Layer', 'LayeredEffect', 'LayeredEffectBuilder',

    # Keyword System (CR 1100+)
    'KeywordManager', 'Keyword', 'KeywordHandler', 'parse_keywords_from_text',

    # Replacement Effects (CR 910)
    'ReplacementManager', 'ReplacementEffectCR', 'ReplacementEffectResult',
    'ReplacementEventType', 'ReplacementBuilder',

    # Triggers with APNAP (CR 906)
    'APNAPTriggerManager', 'TriggerInstance', 'TriggeredAbility', 'TriggerType', 'TriggerBuilder',

    # Choice System (CR 903.2)
    'ChoiceManager', 'Choice', 'ChoiceType', 'ChoiceState', 'ChoiceUIMessage',

    # Integration
    'RulesEngine', 'enhance_engine',
]
