"""
Auto-generated card scripts for MOA

Generated using CR-compliant ability system.
"""

# Core imports
from .. import ScriptRegistry
from ..rules_bridge import (
    RulesCardScript,
    AbilityFactory, EffectBuilder,
    ActivateAbility, AutomaticAbility, ContinuousAbility, WillAbility, JudgmentAbility,
    TriggerCondition, EffectDuration, KeywordAbility,
    TargetRequirement, TargetFilter, TargetZone, TargetController,
    Condition, ConditionType, ConditionBuilder,
    ContinuousEffect, RulesEffect, EffectAction,
    ModalAbility, IncarnationCost, AwakeningCost,
)
from ...models import Attribute, WillCost


@ScriptRegistry.register("MOA-001")
class AlmeriusTheMagusOfLight(RulesCardScript):
    """
    Almerius, the Magus of Light
    Quickcast (You may play this card anytime you can play a Spell:Chant-Instant .)
    Enter : Put a knowledge counter on this card.
    Continuous : Whenever another Six Sages enters your field, put a knowledge counter on this card.
    Activate Remove a knowledge counter from this card: Remove target attacking resonator from the game.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Put a knowledge counter on this card.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("knowledge")],
            is_mandatory=True,
        ))

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Whenever another Six Sages enters your f",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("knowledge")],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="(You may play this card anytime you can ",
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Remove a knowledge counter from this car",
            effects=[EffectBuilder.remove_from_game()],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.QUICKCAST



@ScriptRegistry.register("MOA-002")
class DuetOfLight(RulesCardScript):
    """
    Duet of Light
    Remove target resonator from the game.
    As an additional cost to play this card, rest two recovered light resonators you control.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME
        # Remove target resonator from the game.




@ScriptRegistry.register("MOA-003")
class GrimmTheHeroicKingOfAspiration(RulesCardScript):
    """
    Grimm, the Heroic King of Aspiration
    Other light resonators you control gain [+200/+200].
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="Other light resonators you con",
        ))




@ScriptRegistry.register("MOA-004")
class KaguyaTheTaleOfTheBambooCutter(RulesCardScript):
    """
    Kaguya, the Tale of the Bamboo Cutter
    Activate{1} {Rest} : Put a knowledge counter on target Six Sages.
    Activate Remove three knowledge counters from any number of resonators you control: Remove target resonator from the game.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{1} {Rest} : Put a knowledge counter on ",
            tap_cost=True,
            effects=[EffectBuilder.add_counter("knowledge")],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Remove three knowledge counters from any",
            effects=[EffectBuilder.remove_from_game()],
        ))




@ScriptRegistry.register("MOA-005")
class LumiaTheSaintLadyOfWorldRebirth(RulesCardScript):
    """
    Lumia, the Saint Lady of World Rebirth
    Banish this card: You gain life equal to the damage that was dealt to you this turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish this card: You gain life equal to",
            effects=[EffectBuilder.gain_life(0)],
        ))




@ScriptRegistry.register("MOA-006")
class PandoraThePrincessOfHistoryChanter(RulesCardScript):
    """
    Pandora, the Princess of History Chanter
    Awakening{W} {W} : When this card enters your field, search your main deck for a card named " Grimm, the Heroic King of Aspiration " and put it into your field. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(light=2)
        # Enhanced effect triggers when awakening cost is paid

        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # Awakening{W} {W} : When this card enters your field, search your main 


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("MOA-007")
class PandorasBoxOfHope(RulesCardScript):
    """
    Pandora's Box of Hope
    At the beginning of your main phase, remove the top card of your main deck from the game face down. You may look at that card at any time.
    Banish this card: Put a resonator or Addition:Field card removed by this card into your field rested.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish this card: Put a resonator or Add",
            effects=[],
        ))

        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME
        # At the beginning of your main phase, remove the top card of your main 




@ScriptRegistry.register("MOA-008")
class ShiningBamboo(RulesCardScript):
    """
    Shining Bamboo
    Enter : Search your main deck for a card name " Kaguya, the Tale of the Bamboo Cutter ", reveal it and put it into your hand. Then shuffle your main deck.
    Activate{Rest} : Recover target resonator named " Kaguya, the Tale of the Bamboo Cutter ".
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Search your main deck for a card name \" ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_to_hand(), EffectBuilder.search(destination="hand")],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Recover target resonator named ",
            tap_cost=True,
            effects=[EffectBuilder.recover()],
        ))




@ScriptRegistry.register("MOA-009")
class TemporalSpellOfMillennia(RulesCardScript):
    """
    Temporal Spell of Millennia
    Remove target Cthulhu resonator from the game.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME
        # Remove target Cthulhu resonator from the game.




@ScriptRegistry.register("MOA-010")
class ZeroTheFlashingMagewarrior(RulesCardScript):
    """
    Zero, the Flashing Mage-Warrior
    Quickcast (You may play this card anytime you can play a Spell:Chant-Instant .)
    Enter : Put a knowledge counter on this card.
    Continuous : Whenever another Six Sages enters your field, put a knowledge counter on this card.
    Activate Remove a knowledge counter from this card: Prevent the next 300 damage that would be dealt to target resonator this turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Put a knowledge counter on this card.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("knowledge")],
            is_mandatory=True,
        ))

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Whenever another Six Sages enters your f",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("knowledge")],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="(You may play this card anytime you can ",
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Remove a knowledge counter from this car",
            effects=[],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.QUICKCAST



@ScriptRegistry.register("MOA-011")
class Amenohabakiri(RulesCardScript):
    """
    Ame-no-Habakiri
    Continuous : Added resonator gains [+400/+400].
    Continuous : Whenever added resonator deals damage to a resonator your opponent controls, this card deals that much damage to that resonator's controller.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Whenever added resonator deals damage to",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=400,
            def_=400,
            name="Added resonator gains [+400/+4",
        ))




@ScriptRegistry.register("MOA-012")
class BlazerTheAwakener(RulesCardScript):
    """
    Blazer, the Awakener
    Swiftness (This card can attack and play its{Rest} abilities the same turn it enters a field.)
    Whenever a resonator that was dealt damage by this card this turn is put into a graveyard, recover this card. This ability triggers only once per turn.
    {R} : This card gains First Strike until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Whenever a resonator that was dealt dama",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{R} : This card gains First Strike until",
            will_cost=WillCost(fire=1),
            effects=[EffectBuilder.grant_keyword(KeywordAbility.FIRST_STRIKE)],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FIRST_STRIKE | KeywordAbility.SWIFTNESS



@ScriptRegistry.register("MOA-013")
class CthughaTheLivingFlame(RulesCardScript):
    """
    Cthugha, the Living Flame
    Swiftness (This card can attack and play its{Rest} abilities the same turn it enters a field.)
    Incarnation{R} (You may banish one fire resonator rather than pay this card's cost.)
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Incarnation alternative cost
        self.register_alternative_cost(IncarnationCost(
            required_attributes=[Attribute.FIRE],
            banish_count=1,
        ))

        # [Continuous] ability
        # Continuous effect with: BANISH
        # Incarnation{R} (You may banish one fire resonator rather than pay this


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.SWIFTNESS | KeywordAbility.INCARNATION



@ScriptRegistry.register("MOA-014")
class EmissaryOfAnotherDimension(RulesCardScript):
    """
    Emissary of Another Dimension
    When this card enters your field, recover target resonator.
    Banish this card: Destroy target card in a chant-standby area.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When this card enters your field, recove",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.recover()],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish this card: Destroy target card in",
            effects=[EffectBuilder.destroy()],
        ))




@ScriptRegistry.register("MOA-015")
class FetalMovementInOuterWorld(RulesCardScript):
    """
    Fetal Movement in Outer World
    Remove all cards in target player's graveyard from the game. This card deals 100 damage to your opponent for each resonator removed this way.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE, REMOVE_FROM_GAME
        # Remove all cards in target player\'s graveyard from the game. This card




@ScriptRegistry.register("MOA-016")
class Ghostflame(RulesCardScript):
    """
    Ghostflame
    This card deals 300 damage to target player or resonator.
    Activate{R} {R} {1} : Put this card from your graveyard into your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{R} {R} {1} : Put this card from your gr",
            will_cost=WillCost(fire=2, generic=1),
            effects=[EffectBuilder.return_to_hand()],
        ))

        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE
        # This card deals 300 damage to target player or resonator.




@ScriptRegistry.register("MOA-017")
class LittleRedTheHopeOfMillennia(RulesCardScript):
    """
    Little Red, the Hope of Millennia
    Awakening{R} : When this card enters your field, search your main deck for a card with "Granny" in its name, reveal it and put it into your field. Then shuffle your main deck.
    {Rest} , discard a card with "Apple" in its name: This card deals 1000 damage to target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(fire=1)
        # Enhanced effect triggers when awakening cost is paid

        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE, DISCARD
        # {Rest} , discard a card with \"Apple\" in its name: This card deals 1000


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("MOA-018")
class MilestTheInvisibleGhostlyFlame(RulesCardScript):
    """
    Milest, the Invisible Ghostly Flame
    Enter : Put a knowledge counter on this card.
    Continuous : Whenever another Six Sages enters your field, put a knowledge counter on this card.
    Activate Remove a knowledge counter from this card: This card deals 300 damage to target player or resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Put a knowledge counter on this card.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("knowledge")],
            is_mandatory=True,
        ))

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Whenever another Six Sages enters your f",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("knowledge")],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Remove a knowledge counter from this car",
            effects=[EffectBuilder.deal_damage(300), EffectBuilder.deal_damage(300)],
        ))




@ScriptRegistry.register("MOA-019")
class SusanowoTheTenfistSword(RulesCardScript):
    """
    Susanowo, the Ten-Fist Sword
    Swiftness (This card can attack and play its{Rest} abilities the same turn it enters a field.)
    Pierce
    Continuous : If your opponent controls a Dragon, you may pay{R} {R} {R} less to play this card.
    Enter : You may add a card named " Ame-no-Habakiri " from your hand to this card.
    Enter : This card deals damage equal to its ATK to target resonator your opponent controls.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="This card deals damage equal to its ATK ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.deal_damage(0)],
            is_mandatory=True,
        ))

        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # If your opponent controls a Dragon, you may pay{R} {R} {R} less to pla


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.PIERCE | KeywordAbility.SWIFTNESS



@ScriptRegistry.register("MOA-020")
class Wormhole(RulesCardScript):
    """
    Wormhole
    When this card enters your field, you may put a resonator from your hand into your field. It gains Swiftness until end of turn. At the end of turn, banish it.
    {1} {X} ,{Rest} : Put a resonator with total cost X or less from your hand into your field. It gains Swiftness until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Activated ability with X cost
        self.register_ability(ActivateAbility(
            name="{1} {X} ,{Rest} : Put a resonator with t",
            tap_cost=True,
            x_cost=True,
            generic_cost=1,
            effects=[EffectBuilder.grant_keyword(KeywordAbility.SWIFTNESS), EffectBuilder.put_into_field_x_cost()],
            uses_x=True,  # Effect uses X value from cost
        ))

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When this card enters your field, you ma",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.grant_keyword(KeywordAbility.SWIFTNESS)],
            is_mandatory=False,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.SWIFTNESS



@ScriptRegistry.register("MOA-021")
class AlicesPursuit(RulesCardScript):
    """
    Alice's Pursuit
    Return target resonator your opponent controls with total cost 5 or more to its owner's hand. Draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DRAW, RETURN_TO_HAND
        # Return target resonator your opponent controls with total cost 5 or mo




@ScriptRegistry.register("MOA-022")
class AlicesSoldier(RulesCardScript):
    """
    Alice's Soldier
    This card cannot be targeted by spells or abilities.
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("MOA-023")
class EmperorOfMillennia(RulesCardScript):
    """
    Emperor of Millennia
    Activate{Rest} : Draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Draw a card.",
            tap_cost=True,
            effects=[EffectBuilder.draw(1)],
        ))




@ScriptRegistry.register("MOA-024")
class HouseOfTheOldMan(RulesCardScript):
    """
    House of the Old Man
    Continuous : Magic stones you control gain " Activate{Rest} : Produce one will of any attribute.".
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_continuous_effect(ContinuousEffect(
            name="Magic stones you control gain \" Activate",
            affects_self_only=False,
            # Group buff - affects other cards you control
        ))




@ScriptRegistry.register("MOA-025")
class LunyaTheLiarGirl(RulesCardScript):
    """
    Lunya, the Liar Girl
    When this card enters your field, destroy target Cthulhu.
    Whenever a resonator is put into a graveyard from your field, recover this card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When this card enters your field, destro",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Whenever a resonator is put into a grave",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MOA-026")
class MoojdartTheQueenOfFantasyWorld(RulesCardScript):
    """
    Moojdart, the Queen of Fantasy World
    Enter : Put two knowledge counters on this card.
    Continuous : Whenever another Six Sages enters your field, put two knowledge counters on this card.
    Activate Remove a knowledge counter from this card: Rest target resonator.
    Activate Remove two knowledge counters from this card: Draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Remove a knowledge counter from this car",
            effects=[EffectBuilder.rest()],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Remove two knowledge counters from this ",
            effects=[EffectBuilder.draw(1)],
        ))




@ScriptRegistry.register("MOA-027")
class MoonIncarnation(RulesCardScript):
    """
    Moon Incarnation
    Search your main deck for a Moon addition, reveal it and put it into your hand. Then shuffle your main deck.
    Awakening{2} : You may put a Moon addition from your hand into your field.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(generic=2)
        # Enhanced effect triggers when awakening cost is paid

        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND, SEARCH
        # Search your main deck for a Moon addition, reveal it and put it into y


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("MOA-028")
class OracleOfTsukuyomi(RulesCardScript):
    """
    Oracle of Tsukuyomi
    When this card is put into your graveyard from your field, reveal the top card of your main deck. If it's a Wererabbit, put it into your field. Otherwise, put it into your graveyard.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When this card is put into your graveyar",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MOA-029")
class PurplemistTheFantasyDragon(RulesCardScript):
    """
    Purplemist, the Fantasy Dragon
    Continuous : This card cannot be targeted by spells or abilities.
    Flying (This card cannot be blocked by J/resonators without Flying .)
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.BARRIER | KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("MOA-030")
class TransparentMoon(RulesCardScript):
    """
    Transparent Moon
    Magic stones with non-will activate abilities don't recover during recovery phase.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REMOVE_ABILITY
        # Magic stones with non-will activate abilities don\'t recover during rec




@ScriptRegistry.register("MOA-031")
class BastetTheElderGod(RulesCardScript):
    """
    Bastet, the Elder God
    Continuous : This card gains [+100/+100] for each card in your opponent's graveyard.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=100,
            def_=100,
            name="This card gains [+100/+100] fo",
        ))




@ScriptRegistry.register("MOA-032")
class ChristieTheWardenOfSanctuary(RulesCardScript):
    """
    Christie, the Warden of Sanctuary
    Other Elves you control cannot be targeted by spells or abilities your opponent controls.
    Rest five recovered Elves you control: You gain 500 life and draw two cards.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Rest five recovered Elves you control: Y",
            tap_cost=True,
            effects=[EffectBuilder.gain_life(500)],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("MOA-033")
class FiethsingTheElvishOracle(RulesCardScript):
    """
    Fiethsing, the Elvish Oracle
    Quickcast (You may play this card anytime you can play a Spell:Chant-Instant .)
    Enter : Put a knowledge counter on this card.
    Continuous : Whenever another Six Sages enters your field, put a knowledge counter on this card.
    Activate Remove a knowledge counter from this card: Cancel target spell unless its controller pays{1} .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Put a knowledge counter on this card.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("knowledge")],
            is_mandatory=True,
        ))

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Whenever another Six Sages enters your f",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("knowledge")],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="(You may play this card anytime you can ",
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Remove a knowledge counter from this car",
            effects=[EffectBuilder.cancel()],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.QUICKCAST



@ScriptRegistry.register("MOA-034")
class HanselAndGretel(RulesCardScript):
    """
    Hansel and Gretel
    When this card enters your field, draw a card and put the top card of your magic stone deck into your magic stone area rested.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When this card enters your field, draw a",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.draw(1)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MOA-035")
class LeavesOfYggdrasil(RulesCardScript):
    """
    Leaves of Yggdrasil
    When added resonator is put into a graveyard from a field, put that resonator into it owner's field.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: PUT_INTO_FIELD
        # When added resonator is put into a graveyard from a field, put that re




@ScriptRegistry.register("MOA-036")
class LiberateTheWorld(RulesCardScript):
    """
    Liberate the World
    Look at the top three cards of your main deck. Put one of them into your hand and remove the rest from the game face down.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND, REMOVE_FROM_GAME
        # Look at the top three cards of your main deck. Put one of them into yo




@ScriptRegistry.register("MOA-037")
class MelfeeTheSuccessorOfSacredWind(RulesCardScript):
    """
    Melfee, the Successor of Sacred Wind
    Rest two recovered Elves you control: Produce one will of any attribute.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Rest two recovered Elves you control: Pr",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.VOID)],
        ))




@ScriptRegistry.register("MOA-038")
class RefarthTheWindCastle(RulesCardScript):
    """
    Refarth, the Wind Castle
    Continuous : Prevent all damage that would be dealt by normal spells to resonators you control.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: PREVENT_DAMAGE
        # Prevent all damage that would be dealt by normal spells to resonators 




@ScriptRegistry.register("MOA-039")
class ScheherazadeTheTellerOfTheCrimsonMoon(RulesCardScript):
    """
    Scheherazade, the Teller of the Crimson Moon
    Enter : Choose a race. As long as you control this card, J/resonators of the chosen race cannot attack you.
    Activate{G} {G} {3} ,{Rest} : Remove target resonator from the game.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{G} {G} {3} ,{Rest} : Remove target reso",
            tap_cost=True,
            will_cost=WillCost(wind=2, generic=3),
            effects=[EffectBuilder.remove_from_game()],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.CANNOT_ATTACK



@ScriptRegistry.register("MOA-040")
class WindOfGods(RulesCardScript):
    """
    Wind of Gods
    Put target fire or darkness resonator on top of its owner's main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: PUT_ON_TOP_OF_DECK
        # Put target fire or darkness resonator on top of its owner\'s main deck.




@ScriptRegistry.register("MOA-041")
class AriaTheLastVampire(RulesCardScript):
    """
    Aria, the Last Vampire
    When this card is put into a graveyard from your field, put target Vampire card with total cost 2 or less from your graveyard into your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When this card is put into a graveyard f",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_to_hand()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MOA-042")
class BookOfEibon(RulesCardScript):
    """
    Book of Eibon
    When this card enters field, put target resonator from a graveyard into your field.
    When this card leaves your field, banish the resonator put into your field by this card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When this card enters field, put target ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MOA-043")
class DarkPulse(RulesCardScript):
    """
    Dark Pulse
    Destroy all resonators with total cost 2 or less.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DESTROY
        # Destroy all resonators with total cost 2 or less.




@ScriptRegistry.register("MOA-044")
class EibonTheMage(RulesCardScript):
    """
    Eibon, the Mage
    Awakening{B} : Enter : Search your main deck for a card named " Book of Eibon ", reveal it and put it into your hand. Then shuffle your main deck.
    Activate{B} {B} {1} : Target resonator gains [-400/-400] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(darkness=1)
        # Enhanced effect triggers when awakening cost is paid

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{B} {B} {1} : Target resonator gains [-4",
            will_cost=WillCost(darkness=2, generic=1),
            effects=[EffectBuilder.buff(-400, -400, EffectDuration.UNTIL_END_OF_TURN)],
        ))

        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND, SEARCH
        # Awakening{B} : Enter : Search your main deck for a card named \" Book o


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("MOA-045")
class GrusbalestaTheKeeperOfMagicStones(RulesCardScript):
    """
    Grusbalesta, the Keeper of Magic Stones
    Enter : Put a knowledge counter on this card.
    Continuous : Whenever another Six Sages enters your field, put a knowledge counter on this card.
    Activate Remove a knowledge counter from this card: Target resonator gains [+0/-400] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Put a knowledge counter on this card.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("knowledge")],
            is_mandatory=True,
        ))

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Whenever another Six Sages enters your f",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("knowledge")],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Remove a knowledge counter from this car",
            effects=[EffectBuilder.buff(0, -400, EffectDuration.UNTIL_END_OF_TURN)],
        ))




@ScriptRegistry.register("MOA-046")
class HazzardTheDarkForestAugur(RulesCardScript):
    """
    Hazzard, the Dark Forest Augur
    This card cannot be targeted by spells or abilities.
    At the beginning of your main phase, this card deals 200 damage to target player or resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE
        # At the beginning of your main phase, this card deals 200 damage to tar


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("MOA-047")
class MephistophelesTheDemonCollaborator(RulesCardScript):
    """
    Mephistopheles, the Demon Collaborator
    {Rest} : Target resonator gains [+200/+0] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Target resonator gains [+200/+0",
            tap_cost=True,
            effects=[EffectBuilder.buff(200, 0, EffectDuration.UNTIL_END_OF_TURN)],
        ))




@ScriptRegistry.register("MOA-048")
class MountImmortal(RulesCardScript):
    """
    Mount Immortal
    Continuous : Non-darkness resonators gain [-200/-200].
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=-200,
            def_=-200,
            name="Non-darkness resonators gain [",
        ))




@ScriptRegistry.register("MOA-049")
class NyarlathotepTheUsurper(RulesCardScript):
    """
    Nyarlathotep, the Usurper
    Incarnation{B} ,{B} or{R} (You may banish one darkness resonator and one fire or darkness resonator rather than pay this card's cost.)
    Enter : You may look at target player's hand and choose a card. He or she discards that card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Incarnation alternative cost
        self.register_alternative_cost(IncarnationCost(
            required_attributes=[Attribute.DARKNESS, Attribute.DARKNESS, Attribute.FIRE],
            banish_count=2,
        ))

        # [Continuous] ability
        # Continuous effect with: BANISH
        # Incarnation{B} ,{B} or{R} (You may banish one darkness resonator and o


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.INCARNATION



@ScriptRegistry.register("MOA-050")
class RitualOfMillennia(RulesCardScript):
    """
    Ritual of Millennia
    Choose target resonator from a graveyard that was put into that zone from a field this turn and put it into it owner's field.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: PUT_INTO_FIELD
        # Choose target resonator from a graveyard that was put into that zone f



