"""
Auto-generated card scripts for TAT

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


@ScriptRegistry.register("TAT-001")
class BreathOfTheGod(RulesCardScript):
    """
    Breath of the God
    You may pay{W} {1} less to play this card, if it targets a Saint.
    Target J/resonator you control cannot be targeted by spells or abilities until end of turn. Draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # You may pay{W} {1} less to play this card, if it targets a Saint.

        # [Continuous] ability
        # Continuous effect with: DRAW
        # Target J/resonator you control cannot be targeted by spells or abiliti


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("TAT-002")
class CaterinaTheSaintOfFantasy(RulesCardScript):
    """
    Caterina, the Saint of Fantasy
    Continuous : Other resonators you control gain [+100/+100].
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=100,
            def_=100,
            name="Other resonators you control g",
        ))




@ScriptRegistry.register("TAT-003")
class DonQuijoteTheWanderingKnight(RulesCardScript):
    """
    Don Quijote, the Wandering Knight
    Awakening{W} (You may pay an additional{W} as you play this card. If you do, this card gains the following ability.) Enter : Resonators you control cannot be destroyed until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(light=1)
        # Enhanced effect triggers when awakening cost is paid

        # [Continuous] ability
        # Continuous effect with: GRANT_ABILITY
        # Awakening{W} (You may pay an additional{W} as you play this card. If y


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING | KeywordAbility.INDESTRUCTIBLE



@ScriptRegistry.register("TAT-004")
class GrimmTheAvengerOfFairyTales(RulesCardScript):
    """
    Grimm, the Avenger of Fairy Tales
    Enter : Choose target resonator: Remove it from the game if it's darkness. Otherwise, it gains [+200/+200] until end of turn.
    Awakening{W} : Enter : If you J/ruler is " Sacred Princess of Guidance " or " Lumia, the Creator of Hope ", J/resonators your opponent controls lose all abilities until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(light=1)
        # Enhanced effect triggers when awakening cost is paid

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Choose target resonator: Remove it from ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.remove_from_game(), EffectBuilder.buff(200, 200, EffectDuration.UNTIL_END_OF_TURN)],
            is_mandatory=True,
        ))

        # [Continuous] ability
        # Continuous effect with: REMOVE_ABILITY
        # Awakening{W} : Enter : If you J/ruler is \" Sacred Princess of Guidance


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("TAT-005")
class GuardianOfTower(RulesCardScript):
    """
    Guardian of Tower
    Continuous : Addition:Field cards you control cannot be targeted by spells or abilities your opponent controls.
    Continuous : If you control a Tower, this card gains [+0/+600].
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: MODIFY_DEF
        # If you control a Tower, this card gains [+0/+600].


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("TAT-006")
class JeanneDarcTheAwakeningPurity(RulesCardScript):
    """
    Jeanne d'Arc, the Awakening Purity
    Continuous : Each turn, prevent the first damage that would be dealt to a Fantasy or Human J/resonator you control.
    Awakening{W} : Enter : You may put a nonspell Fantasy Card from your hand into your field. (You may pay an additional{W} as you play this card. If you do, this card gains the following ability.)
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(light=1)
        # Enhanced effect triggers when awakening cost is paid

        # [Continuous] ability
        # Continuous effect with: GRANT_ABILITY
        # Awakening{W} : Enter : You may put a nonspell Fantasy Card from your h


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("TAT-007")
class JumpToTheSky(RulesCardScript):
    """
    Jump to the Sky
    Trigger When a resonator you control deals damage to your opponent: Recover that resonator. You may put three hope counters on a " Lumiel, the Tower of Hope " you control. (Pay{2} to put this card into your chant-standby area. You may play this from the next turn if it fulfills Trigger condition and you control magic stones equal or more than its cost.)
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (DEALS_DAMAGE)
        self.register_ability(AutomaticAbility(
            name="When a resonator you control deals damag",
            trigger_condition=TriggerCondition.DEALS_DAMAGE,
            effects=[],
            is_mandatory=False,
        ))




@ScriptRegistry.register("TAT-008")
class LightOfLumia(RulesCardScript):
    """
    Light of Lumia
    If your J/ruler is " Sacred Princess of Guidance " or " Lumia, the Creator of Hope ", you may pay{2} less to play this card.
    Choose one - Rest all non-light, non-Fairy Tale resonators; or remove target non-light, non-Fairy Tale resonator from the game.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Modal ability: Choose 1
        modal_choices = [
            ("remove target non-light, non-f", EffectBuilder.remove_from_game()),
        ]
        self.register_ability(ModalAbility(
            name="Modal Choice",
            choices=modal_choices,
            choose_count=1,
        ))

        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # If your J/ruler is \" Sacred Princess of Guidance \" or \" Lumia, the Cre

        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME
        # Choose one - Rest all non-light, non-Fairy Tale resonators; or remove 




@ScriptRegistry.register("TAT-009")
class LonginusTheHolyLance(RulesCardScript):
    """
    Longinus, the Holy Lance
    Continuous : Resonator with this gains [+500/+500], cannot be targeted by darkness spells or darkness card's abilities and prevent all damage that would be dealt to it by darkness cards.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=500,
            def_=500,
            name="Resonator with this gains [+50",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("TAT-010")
class LumielTheTowerOfHope(RulesCardScript):
    """
    Lumiel, the Tower of Hope
    Continuous : At the beginning of your main phase, put hope counters equal to the number of resonators you control on this card. Then, if there are ten or more hope counters on this card, banish it and destroy all resonators and additions your opponent controls.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DESTROY
        # At the beginning of your main phase, put hope counters equal to the nu




@ScriptRegistry.register("TAT-011")
class MarchOfSaints(RulesCardScript):
    """
    March of Saints
    Light resonators you control gain [+300/+0] and First Strike until end of turn. If you control a Saint, they cannot be blocked until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=300,
            def_=0,
            name="Light resonators you control g",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FIRST_STRIKE | KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("TAT-012")
class PureSpiritOfFantasy(RulesCardScript):
    """
    Pure Spirit of Fantasy
    """

    pass


@ScriptRegistry.register("TAT-013")
class RealmOfPureSpirits(RulesCardScript):
    """
    Realm of Pure Spirits
    Continuous : Recovered resonators you control cannot be targeted by spells or abilities your opponent controls.
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("TAT-014")
class SacredPrincessOfGuidance(RulesCardScript):
    """
    Sacred Princess of Guidance
    J-Activate Pay{W} . Play this ability only if you control " Almerius, the Levitating Stone ".
    J-Activate Pay{W} {W} {1} .
    Activate{Rest} : You gain 300 life.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            will_cost=WillCost(light=1),
            j_ruler_code="TAT-014J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} . Play this ability only if you c",
            will_cost=WillCost(light=1),
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} {W} {1} .",
            will_cost=WillCost(light=2, generic=1),
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : You gain 300 life.",
            tap_cost=True,
            effects=[EffectBuilder.gain_life(300)],
        ))




@ScriptRegistry.register("TAT-014J")
class LumiaTheCreatorOfHope(RulesCardScript):
    """
    Lumia, the Creator of Hope
    Continuous : Once per turn, you may play a card from your removed from the game zone.
    Activate Pay{0} : If there are no cards in your removed from this game zone, remove top three cards of your main deck from the game face down. You may look at them at any time.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{0} : If there are no cards in your r",
            effects=[EffectBuilder.remove_from_game()],
        ))




@ScriptRegistry.register("TAT-015")
class SacredScepterOfExorcism(RulesCardScript):
    """
    Sacred Scepter of Exorcism
    Continuous : Resonator with this gains " Activate{Rest} : Rest target resonator. If it's a Demon, it cannot be recovered as long as this card is in a field."
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REST
        # Resonator with this gains \" Activate{Rest} : Rest target resonator. If




@ScriptRegistry.register("TAT-016")
class SeekingSkySoldier(RulesCardScript):
    """
    Seeking Sky Soldier
    Flying (While attacking, this card cannot be blocked by J/resonators without Flying .)
    Enter : You may look the top card of your opponent's main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="You may look the top card of your oppone",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=False,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("TAT-017")
class SleepingBeauty(RulesCardScript):
    """
    Sleeping Beauty
    Continuous : You may choose not to recover this card during the recovery phase.
    Activate Pay{1} {Rest} : Resonators you control gain [+200/+200] as long as this card is rested.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{1} {Rest} : Resonators you control g",
            tap_cost=True,
            effects=[EffectBuilder.buff(200, 200, EffectDuration.INSTANT)],
        ))




@ScriptRegistry.register("TAT-018")
class TheQueensButler(RulesCardScript):
    """
    The Queen's Butler
    Continuous Your J/ruler cannot be targeted by your opponent's spells or abilities.
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("TAT-019")
class BeowulfTheBlazingWolf(RulesCardScript):
    """
    Beowulf, the Blazing Wolf
    Continuous : If this card would deal damage to your opponent or to a resonator, it deals double that much instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_continuous_effect(ContinuousEffect(
            name="Double Damage",
            affects_self_only=True,
            # This card deals double damage
        ))




@ScriptRegistry.register("TAT-020")
class BigbangRevolution(RulesCardScript):
    """
    Big-Bang Revolution
    Trigger When a resonator you control is destroyed: Two target resonators gain [+X/+Y] until end of turn, where X is the destroyed resonator's ATK and Y is the destroyed resonator's DEF.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (DESTROYED)
        self.register_ability(AutomaticAbility(
            name="When a resonator you control is destroye",
            trigger_condition=TriggerCondition.DESTROYED,
            effects=[],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-021")
class CardSoldierDiamond(RulesCardScript):
    """
    Card Soldier "Diamond"
    Continuous : When this card is put into a graveyard from your field, it deals 200 damage to target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="When this card is put into a graveyard f",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[EffectBuilder.deal_damage(200)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-022")
class CardSoldierHeart(RulesCardScript):
    """
    Card Soldier "Heart"
    Continuous : If damage would be dealt to a " Queen of Hearts " you control, it's dealt to this card instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: PREVENT_DAMAGE
        # If damage would be dealt to a \" Queen of Hearts \" you control, it\'s de




@ScriptRegistry.register("TAT-023")
class DragonKingsFlame(RulesCardScript):
    """
    Dragon King's Flame
    This card deals 600 damage to target player or resonator. If your J/ruler is " Falltgold, the Dragoon " or " Bahamut, the Dragon King ", it deals 800 damage instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE
        # This card deals 600 damage to target player or resonator. If your J/ru




@ScriptRegistry.register("TAT-024")
class DuelOfTruth(RulesCardScript):
    """
    Duel of Truth
    Target J/resonator you control and target J/resonator your opponent control deal damage equal to their ATK to each other.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE
        # Target J/resonator you control and target J/resonator your opponent co




@ScriptRegistry.register("TAT-025")
class EndlessWar(RulesCardScript):
    """
    Endless War
    Continuous Resonators must attack if able.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_continuous_effect(ContinuousEffect(
            name="Must Attack",
            affects_self_only=True,
            # Forces this card to attack if able
        ))




@ScriptRegistry.register("TAT-026")
class FalltgoldTheDragoon(RulesCardScript):
    """
    Falltgold, the Dragoon
    J-Activate Banish a fire resonator.
    Activate{Rest} : Search your main deck for a Dragon resonator, reveal it and put it into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish a fire resonator.",
            effects=[EffectBuilder.banish()],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Search your main deck for a Dra",
            tap_cost=True,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
        ))




@ScriptRegistry.register("TAT-026J")
class BahamutTheDragonKing(RulesCardScript):
    """
    Bahamut, the Dragon King
    Flying (While attacking, this card cannot be blocked by J/resonator without Flying .)
    Enter This card deals damage to target resonator equal to the ATK of resonator banished for its judgment.
    Activate Banish a fire resonator: This card gains Imperishable until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="This card deals damage to target resonat",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish a fire resonator: This card gains",
            effects=[EffectBuilder.grant_keyword(KeywordAbility.IMPERISHABLE)],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.IMPERISHABLE | KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("TAT-027")
class ForcedGrowth(RulesCardScript):
    """
    Forced Growth
    Continuous : Resonator with this gains [+400/-400].
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=400,
            def_=-400,
            name="Resonator with this gains [+40",
        ))




@ScriptRegistry.register("TAT-028")
class FthagguaTheFlameSpirit(RulesCardScript):
    """
    Fthaggua, the Flame Spirit
    First Strike (While attacking, this card deals its battle damage first to the blocker or attacked object.)
    Continuous : This card gains [+200/+200] for each spell card in your graveyard.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="This card gains [+200/+200] fo",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FIRST_STRIKE



@ScriptRegistry.register("TAT-029")
class GlidingDragonKnight(RulesCardScript):
    """
    Gliding Dragon Knight
    Flying (While attacking, this card cannot be blocked by J/resonators without Flying .)
    Activate{R} : This card gains [+100/+0] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{R} : This card gains [+100/+0] until en",
            will_cost=WillCost(fire=1),
            effects=[EffectBuilder.buff(100, 0, EffectDuration.UNTIL_END_OF_TURN)],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("TAT-030")
class KusanagiSword(RulesCardScript):
    """
    Kusanagi Sword
    Enter : This card deals 600 damage to target resonator.
    Continuous : If resonator with this would deal damage, it deals that much +200 instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="This card deals 600 damage to target res",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.deal_damage(600), EffectBuilder.deal_damage(600)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-031")
class LittleDreadTheFakeRedMoon(RulesCardScript):
    """
    Little Dread, the Fake Red Moon
    Target Attack (This card can attack recovered <J/resonators>.)
    Awakening{R} : Enter : Target resonator gains [+600/-600] until end of turn.
    Awakening{R} {1} : Enter : Recover target resonator. You gain control of it until end of turn. It gains Swiftness until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(fire=1)
        # Enhanced effect triggers when awakening cost is paid

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=600,
            def_=-600,
            name="Awakening{R} : Enter : Target ",
        ))

        # [Continuous] ability
        # Continuous effect with: RECOVER, GRANT_KEYWORD, GAIN_CONTROL
        # Awakening{R} {1} : Enter : Recover target resonator. You gain control 


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.SWIFTNESS | KeywordAbility.AWAKENING | KeywordAbility.TARGET_ATTACK



@ScriptRegistry.register("TAT-032")
class RapidDecay(RulesCardScript):
    """
    Rapid Decay
    Destroy target resonator with total cost 2 or less.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DESTROY
        # Destroy target resonator with total cost 2 or less.




@ScriptRegistry.register("TAT-033")
class RealmOfTheDragonKing(RulesCardScript):
    """
    Realm of the Dragon King
    Continuous : Whenever a non-Dragon resonator comes into a field, this card deals 500 damage to it. If you control " Bahamut, the Dragon King ", this card deals 800 damage instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Whenever a non-Dragon resonator comes in",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.deal_damage(500), EffectBuilder.deal_damage(500)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-034")
class RedbirdOfOmen(RulesCardScript):
    """
    Redbird of Omen
    Flying
    Continuous : At the beginning of your main phase, destroy all resonators with total cost equal to the number of omen counters on this card.
    Continuous : At the end of your turn, put an omen counter on this card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DESTROY
        # At the beginning of your main phase, destroy all resonators with total

        # [Continuous] ability
        # Continuous effect with: ADD_COUNTER, GRANT_ABILITY
        # At the end of your turn, put an omen counter on this card.


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING



@ScriptRegistry.register("TAT-035")
class WickedWitchOfTheWest(RulesCardScript):
    """
    Wicked Witch of the West
    Activate{Rest} : This card deals 200 damage to target resonator.
    Continuous : When this card becomes targeted by water spells or water card's abilities, destroy it.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When this card becomes targeted by water",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : This card deals 200 damage to t",
            tap_cost=True,
            effects=[EffectBuilder.deal_damage(200), EffectBuilder.deal_damage(200)],
        ))




@ScriptRegistry.register("TAT-036")
class YamatanoorochiTheEightDisasters(RulesCardScript):
    """
    Yamata-no-Orochi, the Eight Disasters
    Swiftness
    Target Attack
    Continuous : Attacking doesn't cause this card to rest.
    Continuous : Each of your turns, this card can attack up to eight times.
    Continuous : When this card is put into a graveyard from your field, you may search your main deck for a card named " Kusanagi Sword " and add it to a resonator. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="When this card is put into a graveyard f",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[],
            is_mandatory=False,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.SWIFTNESS | KeywordAbility.TARGET_ATTACK



@ScriptRegistry.register("TAT-037")
class AliceInWonderland(RulesCardScript):
    """
    Alice in Wonderland
    J-Activate Pay any number of will. You cannot choose to pay{0} .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay any number of will. You cannot choos",
            effects=[],
        ))




@ScriptRegistry.register("TAT-037J")
class AliceTheDrifterInTheWorld(RulesCardScript):
    """
    Alice, the Drifter in the World
    Enter : If you paid{W} for doing judgment, you gain 1000 life. If you paid{U} , draw a card. If you paid{B} , target opponent discard a card. If you paid{R} , this card deals 1000 damage to up to one target resonator. If you paid{G} , destroy up to one target addition. If you paid will of each attribute and will produced from " Moojdart, the Fantasy Stone ", this card gains Flying and Swiftness until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="If you paid{W} for doing judgment, you g",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.draw(1), EffectBuilder.deal_damage(1000), EffectBuilder.deal_damage(1000), EffectBuilder.destroy(), EffectBuilder.gain_life(1000), EffectBuilder.discard(1)],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.SWIFTNESS



@ScriptRegistry.register("TAT-038")
class AlicesWorld(RulesCardScript):
    """
    Alice's World
    For each resonator you control that doesn't share any race with other resonators you control, you may pay{1} less to play this card. (For example, if you control a Nightmare resonator and a Fairy Tale resonator, you may pay{2} less.)
    Enter Take an extra turn after this one.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Take an extra turn after this one.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # For each resonator you control that doesn\'t share any race with other 




@ScriptRegistry.register("TAT-039")
class CheshireCatTheGrinningRemnant(RulesCardScript):
    """
    Cheshire Cat, the Grinning Remnant
    Continuous : This card cannot be targeted by spells or abilities.
    Enter : Draw two cards, then put a card from your hand on top of your main deck.
    Continuous : When this card it put into a graveyard from a field, shuffle it into its owner's main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Draw two cards, then put a card from you",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.draw(2), EffectBuilder.put_on_top_of_deck()],
            is_mandatory=True,
        ))

        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="When this card it put into a graveyard f",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[EffectBuilder.shuffle_into_deck()],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("TAT-040")
class CrossroadOfWorlds(RulesCardScript):
    """
    Crossroad of Worlds
    Target resonator loses all abilities and gains all abilities of another target resonator until end of turn. First resonator's ATK and DEF become the same of second resonator until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REMOVE_ABILITY
        # Target resonator loses all abilities and gains all abilities of anothe




@ScriptRegistry.register("TAT-041")
class DestructiveFlow(RulesCardScript):
    """
    Destructive Flow
    Trigger At the end of a turn you're dealt damage: Return all rested resonators your opponent controls to their owner's hand. (Pay{2} to put this card into your chant-standby area. You may play this from the next turn if it fulfills Trigger condition and you control magic stones equal or more than its cost.)
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (TURN_END)
        self.register_ability(AutomaticAbility(
            name="At the end of a turn you\'re dealt damage",
            trigger_condition=TriggerCondition.TURN_END,
            effects=[EffectBuilder.return_to_hand()],
            is_mandatory=False,
        ))




@ScriptRegistry.register("TAT-042")
class DreamsOfWonderland(RulesCardScript):
    """
    Dreams of Wonderland
    Reveal the top of your main deck. If its total cost is odd, return target resonator to its owner's hand. Otherwise, draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DRAW, RETURN_TO_HAND
        # Reveal the top of your main deck. If its total cost is odd, return tar




@ScriptRegistry.register("TAT-043")
class HumptyDumpty(RulesCardScript):
    """
    Humpty Dumpty
    Activate{U} , banish this card: Reveal the top card of your main deck. If it's a resonator, put it into your field. Otherwhise, put in into your graveyard.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{U} , banish this card: Reveal the top c",
            will_cost=WillCost(water=1),
            effects=[EffectBuilder.reveal_top()],
        ))




@ScriptRegistry.register("TAT-044")
class LittleMermaidOfTragicLove(RulesCardScript):
    """
    Little Mermaid of Tragic Love
    Continuous : When this card is put into a graveyard from your field, draw a card.
    Continuous : Your opponent must block this card if able.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="When this card is put into a graveyard f",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[EffectBuilder.draw(1)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-045")
class MadHatter(RulesCardScript):
    """
    Mad Hatter
    Awakening{U} : Enter : Draw a card. (You may pay an additional{U} as you play this card. If you do, this card gains the following ability.)
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(water=1)
        # Enhanced effect triggers when awakening cost is paid

        # [Continuous] ability
        # Continuous effect with: DRAW, GRANT_ABILITY
        # Awakening{U} : Enter : Draw a card. (You may pay an additional{U} as y


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("TAT-046")
class MadTeaparty(RulesCardScript):
    """
    Mad Tea-Party
    Continuous <Tea-Party Madness> Whenever a resonator you control becomes targeted by spells or other abilities other than through <Tea-Party Madness>, choose the new target at random. (Choose at random among all the legal targets including the original one.)
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="<Tea-Party Madness> Whenever a resonator",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-047")
class MarchHare(RulesCardScript):
    """
    March Hare
    Continuous : Whenever this card attacks, reveal the top card of your main deck. If its total cost is even, the next damage this card would deal this turn is dealt to you instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Attack trigger ability
        self.register_ability(AutomaticAbility(
            name="Whenever this card attacks, reveal the t",
            trigger_condition=TriggerCondition.DECLARES_ATTACK,
            effects=[EffectBuilder.reveal_top(), EffectBuilder.redirect_damage()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-048")
class RiinaTheGirlWithNothing(RulesCardScript):
    """
    Riina, the Girl with Nothing
    Activate Pay{0} : Target resonator you control loses all abilities until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{0} : Target resonator you control lo",
            effects=[EffectBuilder.remove_all_abilities()],
        ))




@ScriptRegistry.register("TAT-049")
class SeashoreFisherman(RulesCardScript):
    """
    Seashore Fisherman
    Activate{Rest} : Reveal the top card of your main deck. If it's a resonator, put it back, look the top four cards of your main deck and put them in any order. If it's an addition, put it into your hand. If it's a spell card, rest target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Reveal the top card of your mai",
            tap_cost=True,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.rest(), EffectBuilder.reveal_top()],
        ))




@ScriptRegistry.register("TAT-050")
class ShallowsGiantDolphin(RulesCardScript):
    """
    Shallows Giant Dolphin
    Continuous : Whenever this card blocks, rest target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (DECLARES_BLOCK)
        self.register_ability(AutomaticAbility(
            name="Whenever this card blocks, rest target r",
            trigger_condition=TriggerCondition.DECLARES_BLOCK,
            effects=[EffectBuilder.rest()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-051")
class SleepingRat(RulesCardScript):
    """
    Sleeping Rat
    """

    pass


@ScriptRegistry.register("TAT-052")
class StarMoney(RulesCardScript):
    """
    Star Money
    Continuous : Resonator with this gains [+700/+700] if it has no printed abilities.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=700,
            def_=700,
            name="Resonator with this gains [+70",
        ))




@ScriptRegistry.register("TAT-053")
class WhirlpoolOfKnowledge(RulesCardScript):
    """
    Whirlpool of Knowledge
    Draw cards equal to the number of different attributes among resonators you control. (Cards without attributes don't count.)
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DRAW
        # Draw cards equal to the number of different attributes among resonator




@ScriptRegistry.register("TAT-054")
class WitchsDagger(RulesCardScript):
    """
    Witch's Dagger
    Continuous : Resonator with this gains " Activate Pay{U} {U} {2} {Rest} : Destroy target rested resonator." and " Activate{Rest} , banish this resonator: Draw three cards."
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DRAW, DESTROY
        # Resonator with this gains \" Activate Pay{U} {U} {2} {Rest} : Destroy t




@ScriptRegistry.register("TAT-055")
class BrainlessScarecrow(RulesCardScript):
    """
    Brainless Scarecrow
    Enter : If you control " Heartless Tin Man " or " Cowardly Lion ", put an achievement counter on this card.
    Continuous : This card gains [+300/+300] for each achievement counter on it.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="If you control \" Heartless Tin Man \" or ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("achievement")],
            is_mandatory=True,
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=300,
            def_=300,
            name="This card gains [+300/+300] fo",
        ))




@ScriptRegistry.register("TAT-056")
class CowardlyLion(RulesCardScript):
    """
    Cowardly Lion
    Continuous : This card gains [+300/+300] for each achievement counter on it.
    Continuous : Whenever this card deals damage to your opponent, put an achievement counter on this card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=300,
            def_=300,
            name="This card gains [+300/+300] fo",
        ))

        # Triggered ability (DEALS_DAMAGE)
        self.register_ability(AutomaticAbility(
            name="Whenever this card deals damage to your ",
            trigger_condition=TriggerCondition.DEALS_DAMAGE,
            effects=[EffectBuilder.add_counter("achievement")],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-057")
class CrimsonGirlInTheSky(RulesCardScript):
    """
    Crimson Girl in the Sky
    J-Activate Pay{0} . Play this ability only if you put "Refarth, the Castle of Heaven" into a field this turn.
    J-Activate Pay{G} {G} {1} .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            j_ruler_code="TAT-057J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{0} . Play this ability only if you p",
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{G} {G} {1} .",
            will_cost=WillCost(wind=2, generic=1),
            effects=[],
        ))




@ScriptRegistry.register("TAT-057J")
class LittleRedTheTrueFairyTale(RulesCardScript):
    """
    Little Red, the True Fairy Tale
    Continuous : This card cannot be targeted by darkness or fire spells or darkness or fire card's abilities.
    Continuous : If a spell or ability would increase ATK or DEF of resonators you control, it increases double that much instead.
    Continuous : If a spell or ability would decrease ATK or DEF of resonators you control, it decreases none instead.
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("TAT-058")
class DorothyTheLostGirl(RulesCardScript):
    """
    Dorothy, the Lost Girl
    Continuous : Whenever this card deals damage to your opponent, put the top card of your magic stone deck into your magic stone area.
    Awakening{G} : Enter : Reveal top five cards of your main deck. Put any number of cards named " Heartless Tin Man ", " Brainless Scarecrow ", " Cowardly Lion " and/or " Silver Shoes " among them into your hand. Put the rest on the bottom of your main deck in any order.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(wind=1)
        # Enhanced effect triggers when awakening cost is paid

        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND
        # Awakening{G} : Enter : Reveal top five cards of your main deck. Put an

        # Triggered ability (DEALS_DAMAGE)
        self.register_ability(AutomaticAbility(
            name="Whenever this card deals damage to your ",
            trigger_condition=TriggerCondition.DEALS_DAMAGE,
            effects=[],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("TAT-059")
class Dragonslayer(RulesCardScript):
    """
    Dragonslayer
    Enter : Destroy target Dragon.
    Continuous : If damage would be dealt to the resonator with this, prevent 500 of it.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Destroy target Dragon.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))

        # [Continuous] ability
        # Continuous effect with: PREVENT_DAMAGE
        # If damage would be dealt to the resonator with this, prevent 500 of it




@ScriptRegistry.register("TAT-060")
class EvolutionOfLimits(RulesCardScript):
    """
    Evolution of Limits
    Target resonator gains [+600/+600] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=600,
            def_=600,
            name="Target resonator gains [+600/+",
        ))




@ScriptRegistry.register("TAT-061")
class GardeaTheGuardianDragonOfHeaven(RulesCardScript):
    """
    Gardea, the Guardian Dragon of Heaven
    Enter Search your magic stone deck for a card. Then, shuffle the rest of your magic stone deck and put that card on top of it.
    Activate{Rest} : Target resonator you control gains [+400/+0] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Search your magic stone deck for a card.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Target resonator you control ga",
            tap_cost=True,
            effects=[EffectBuilder.buff(400, 0, EffectDuration.UNTIL_END_OF_TURN)],
        ))




@ScriptRegistry.register("TAT-062")
class GlindaTheFairy(RulesCardScript):
    """
    Glinda, the Fairy
    Enter : Target resonator cannot be blocked until end of turn.
    Activate Banish this card: Cancel target normal spell unless its controller pays{2} .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Target resonator cannot be blocked until",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish this card: Cancel target normal s",
            effects=[],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("TAT-063")
class GuideOfHeaven(RulesCardScript):
    """
    Guide of Heaven
    Activate{Rest} : Reveal the top card of your main deck. If it's an Elf resonator, put it into your hand.
    Awakening{G} : Enter : Search your main deck for an Elf resonator, reveal it and put it into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(wind=1)
        # Enhanced effect triggers when awakening cost is paid

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Reveal the top card of your mai",
            tap_cost=True,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.reveal_top()],
        ))

        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND, SEARCH
        # Awakening{G} : Enter : Search your main deck for an Elf resonator, rev


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("TAT-064")
class HeartlessTinMan(RulesCardScript):
    """
    Heartless Tin Man
    Continuous : This card gains [+300/+300] for each achievement counter on it.
    Continuous : When an addition is added to a resonator you control or an Addition:Field is put into your field, put an achievement counter on this card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When an addition is added to a resonator",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.add_counter("achievement")],
            is_mandatory=True,
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=300,
            def_=300,
            name="This card gains [+300/+300] fo",
        ))




@ScriptRegistry.register("TAT-065")
class OzTheGreatWizard(RulesCardScript):
    """
    Oz, the Great Wizard
    Enter : Search your main deck for a spell card with total cost 1, reveal it and put it into your hand. If its name is " Oz's Magic ", you may play it without paying its cost instead of putting it into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Search your main deck for a spell card w",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
            is_mandatory=False,
        ))




@ScriptRegistry.register("TAT-066")
class OzsMagic(RulesCardScript):
    """
    Oz's Magic
    Put an achievement counter on each of up to two target resonators. If you control " Oz, the Great Wizard ", draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DRAW, ADD_COUNTER
        # Put an achievement counter on each of up to two target resonators. If 




@ScriptRegistry.register("TAT-067")
class PortalOfTruth(RulesCardScript):
    """
    Portal of Truth
    Trigger Anytime: Destroy target resonator if its ATK is different from its printed ATK or its DEF is different from its printed DEF. (Pay{2} to put this card into your chant-standby area. You may play this from the next turn if it fulfills Trigger condition and you control magic stones equal or more than its cost.)
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Anytime: Destroy target resonator if its",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=False,
        ))




@ScriptRegistry.register("TAT-068")
class RealmOfEvolution(RulesCardScript):
    """
    Realm of Evolution
    Continuous : Fairy Tales you control gain [+200/+200].
    Activate{G} , banish this card: Search your main deck for a Fairy Tale resonator, reveal it and put it into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{G} , banish this card: Search your main",
            will_cost=WillCost(wind=1),
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="Fairy Tales you control gain [",
        ))




@ScriptRegistry.register("TAT-069")
class RefarthTheCastleInHeaven(RulesCardScript):
    """
    Refarth, the Castle in Heaven
    Continuous : Resonators you control gain [+100/+100].
    Activate Banish this card: Target resonator gains [+400/+400] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish this card: Target resonator gains",
            effects=[EffectBuilder.buff(400, 400, EffectDuration.UNTIL_END_OF_TURN)],
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=100,
            def_=100,
            name="Resonators you control gain [+",
        ))




@ScriptRegistry.register("TAT-070")
class SilverShoes(RulesCardScript):
    """
    Silver Shoes
    Continuous : Resonator with this gains [+300/+300].
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=300,
            def_=300,
            name="Resonator with this gains [+30",
        ))




@ScriptRegistry.register("TAT-071")
class WolfInTheSky(RulesCardScript):
    """
    Wolf in the Sky
    Continuous : Whenever this card attacks, it gains [+400/+0] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Attack trigger ability
        self.register_ability(AutomaticAbility(
            name="Whenever this card attacks, it gains [+4",
            trigger_condition=TriggerCondition.DECLARES_ATTACK,
            effects=[EffectBuilder.buff(400, 0, EffectDuration.UNTIL_END_OF_TURN)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-072")
class XeexTheAncientMagic(RulesCardScript):
    """
    Xeex the Ancient Magic
    Choose one. If your J/ruler is " Crimson Girl in the Sky " or " Little Red, the True Fairy Tale ", choose up to four - Target resonator cannot be targeted by spells or abilities until end of turn; or cancel target summon spell; or resonators you control gain [+200/+200] until end of turn; or target player shuffles all magic stones from his or her graveyard into his magic stone deck, then shuffles all other cards from his or her graveyard into his of her main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Modal ability: Choose 1
        modal_choices = [
            ("resonators you control gain [+", EffectBuilder.buff(200, 200, EffectDuration.UNTIL_END_OF_TURN)),
        ]
        self.register_ability(ModalAbility(
            name="Modal Choice",
            choices=modal_choices,
            choose_count=1,
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="Choose one. If your J/ruler is",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("TAT-073")
class AlhaberTheTowerOfDespair(RulesCardScript):
    """
    Al-Haber, the Tower of Despair
    Continuous : When a resonator your opponent controls is put into a graveyard, put a despair counter on this card.
    Continuous : At the beginning of your main phase, if there are seven or more despair counters on this card, banish it and you may search your main deck for up to two darkness resonators and play them without paying their cost. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="When a resonator your opponent controls ",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[EffectBuilder.add_counter("despair")],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-074")
class CardSoldierClub(RulesCardScript):
    """
    Card Soldier "Club"
    Enter : Reveal the top four cards of your main deck. Put a Card Soldier card among them into your hand. Put the rest into your graveyard.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Reveal the top four cards of your main d",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_from_graveyard()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("TAT-075")
class CardSoldierSpade(RulesCardScript):
    """
    Card Soldier "Spade"
    Continuous : This card gains [+200/+200] for each other Card Soldier you control.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="This card gains [+200/+200] fo",
        ))




@ScriptRegistry.register("TAT-076")
class DeathSentenceFromTheQueen(RulesCardScript):
    """
    Death Sentence from the Queen
    Trigger While a resonator your opponent controls is attacking: Your opponent banish a non-attacking resonator he or she controls. You gain life equal to its DEF. (Pay{2} to put this card into your chant-standby area. You may play this from the next turn if it fulfills Trigger condition and you control magic stones equal or more than its cost.)
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="While a resonator your opponent controls",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.banish(), EffectBuilder.opponent_banishes()],
            is_mandatory=False,
        ))




@ScriptRegistry.register("TAT-077")
class DemonsCurse(RulesCardScript):
    """
    Demon's Curse
    Continuous : Resonator with this gains [-200/-200]. When the resonator with this is put into a graveyard from a field, this card deals 500 damage to that resonator's controller.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=-200,
            def_=-200,
            name="Resonator with this gains [-20",
        ))




@ScriptRegistry.register("TAT-078")
class EbonyDevil(RulesCardScript):
    """
    Ebony Devil
    Continuous : At the end of your turn, this card deals 200 damage to you.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE, GRANT_ABILITY
        # At the end of your turn, this card deals 200 damage to you.




@ScriptRegistry.register("TAT-079")
class EbonyProphet(RulesCardScript):
    """
    Ebony Prophet
    J-Activate Pay{B} . Play this ability only if you control " Grusbalesta, the Sealing Stone ".
    J-Activate Pay{B} {B} {1} .
    Activate{Rest} : Target resonator gains [-300/-300] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            will_cost=WillCost(darkness=1),
            j_ruler_code="TAT-079J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{B} . Play this ability only if you c",
            will_cost=WillCost(darkness=1),
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{B} {B} {1} .",
            will_cost=WillCost(darkness=2, generic=1),
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Target resonator gains [-300/-3",
            tap_cost=True,
            effects=[EffectBuilder.buff(-300, -300, EffectDuration.UNTIL_END_OF_TURN)],
        ))




@ScriptRegistry.register("TAT-079J")
class AbdulAlhazredTheHarbingerOfDespair(RulesCardScript):
    """
    Abdul Alhazred, the Harbinger of Despair
    Entities entering the field under your opponent's control don't cause their own abilities to trigger.
    Activate{0} : Target resonator or addition loses all abilities until end of turn. You may play this ability up to twice per turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{0} : Target resonator or addition loses",
            effects=[EffectBuilder.remove_all_abilities()],
        ))




@ScriptRegistry.register("TAT-080")
class ElderThings(RulesCardScript):
    """
    Elder Things
    Continuous This card gains [+200/+200] for each resonator in all graveyard.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="This card gains [+200/+200] fo",
        ))




@ScriptRegistry.register("TAT-081")
class JokersSuit(RulesCardScript):
    """
    Joker's Suit
    Continuous : Resonator with this gains [+200/+200] and Card Soldier in addition to its own race.
    Continuous : When this card is put into a graveyard from a field, you may add it to a target resonator you control.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="Resonator with this gains [+20",
        ))

        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="When this card is put into a graveyard f",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[],
            is_mandatory=False,
        ))




@ScriptRegistry.register("TAT-082")
class LaplaciaTheDemonOfFate(RulesCardScript):
    """
    Laplacia, the Demon of Fate
    Continuous : You opponent plays with top card of his or her main deck revealed.
    Continuous : You may look at the top card of your main deck at any time.
    Activate{Rest} : Put the top card of your main deck and the top card of your opponent's main deck into their owner's graveyard.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Put the top card of your main d",
            tap_cost=True,
            effects=[],
        ))




@ScriptRegistry.register("TAT-083")
class MephistophelesTheAbyssalTyrant(RulesCardScript):
    """
    Mephistopheles, the Abyssal Tyrant
    Flying Target Attack
    Continuous : When this card becomes targeted by spells or abilities your opponent controls, he or she loses 500 life.
    Continuous : At the end of your turn, banish another resonator you control.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When this card becomes targeted by spell",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Continuous] ability
        # Continuous effect with: BANISH, GRANT_ABILITY
        # At the end of your turn, banish another resonator you control.


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.TARGET_ATTACK



@ScriptRegistry.register("TAT-084")
class Necronomicon(RulesCardScript):
    """
    Necronomicon
    Continuous : You may play cards in your graveyard.
    Continuous : If a card would be put into your graveyard from anywhere, remove it from the game instead.
    Continuous : At the end of your turn, discard your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME
        # If a card would be put into your graveyard from anywhere, remove it fr

        # [Continuous] ability
        # Continuous effect with: GRANT_ABILITY
        # At the end of your turn, discard your hand.




@ScriptRegistry.register("TAT-085")
class NeithardtTheDemonKnight(RulesCardScript):
    """
    Neithardt, the Demon Knight
    Continuous : This card cannot be targeted by light spells or light card's abilities and prevent all damage that would be dealt to this card by light cards.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: PREVENT_DAMAGE
        # This card cannot be targeted by light spells or light card\'s abilities


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("TAT-086")
class QueenOfHearts(RulesCardScript):
    """
    Queen of Hearts
    Continuous : You may pay{1} less to play Card Soldier resonators.
    Enter : Put up to one target card named "Card Soldier "Spade"", up to one target card named "Card Soldier "Club"", up to one target card named "Card Soldier "Diamond"" and up to one target card named "Card Soldier "Heart"" from your graveyard into your hand.
    Activate{Rest} , banish two Card Soldiers: Destroy target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Put up to one target card named \"Card So",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_from_graveyard()],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} , banish two Card Soldiers: Destr",
            tap_cost=True,
            effects=[EffectBuilder.destroy()],
        ))

        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # You may pay{1} less to play Card Soldier resonators.




@ScriptRegistry.register("TAT-087")
class SpireShadowDrake(RulesCardScript):
    """
    Spire Shadow Drake
    Flying (While attacking this card cannot be blocked by J/resonators without Flying .)
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("TAT-088")
class StoningToDeath(RulesCardScript):
    """
    Stoning to Death
    Destroy target resonator
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DESTROY
        # Destroy target resonator




@ScriptRegistry.register("TAT-089")
class SummoningArtOfAlhazred(RulesCardScript):
    """
    Summoning Art of Alhazred
    Search your main deck for a Demon resonator, reveal it and put it into your hand. Then shuffle your main deck. If your J/ruler is " Ebony Prophet " or " Abdul Alhazred, the Harbinger of Despair ", you may pay{B} {B} less to play cards with the same name as the card you searched until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND, SEARCH
        # Search your main deck for a Demon resonator, reveal it and put it into




@ScriptRegistry.register("TAT-090")
class WhisperFromTheAbyss(RulesCardScript):
    """
    Whisper from the Abyss
    Pay any amount of life. Draw a card for each 500 life you lost this way.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DRAW
        # Pay any amount of life. Draw a card for each 500 life you lost this wa




@ScriptRegistry.register("TAT-091")
class AlmeriusTheLevitatingStone(RulesCardScript):
    """
    Almerius, the Levitating Stone
    Activate{Rest} : Produce{W} .
    Activate{W} {Rest} : Target J/resonator gains Flying until end of turn.
    Continuous When you control two or more true magic stones with the same name, banish all but one of them.
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.LIGHT],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{W} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.LIGHT)],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{W} {Rest} : Target J/resonator gains Fl",
            tap_cost=True,
            will_cost=WillCost(light=1),
            effects=[EffectBuilder.grant_keyword(KeywordAbility.FLYING)],
        ))




@ScriptRegistry.register("TAT-092")
class FeethsingTheHolyWindStone(RulesCardScript):
    """
    Feethsing, the Holy Wind Stone
    Activate{Rest} : Produce{G} .
    Continuous When you control two or more true magic stones with the same name, banish all but one of them.
    Activate{G} {Rest} : Target J/resonator cannot be targeted by normal spells your opponents control until end of turn.
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.WIND],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{G} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.WIND)],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{G} {Rest} : Target J/resonator cannot b",
            tap_cost=True,
            will_cost=WillCost(wind=1),
            effects=[],
        ))




@ScriptRegistry.register("TAT-093")
class GrusbalestaTheSealingStone(RulesCardScript):
    """
    Grusbalesta, the Sealing Stone
    Activate{Rest} : Produce{B} .
    Activate{B} {Rest} : Target J/resonator gains [+0/-200] until end of turn.
    Continuous : When you control two or more true magic stones with same name, banish all but one of them.
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.DARKNESS],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{B} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.DARKNESS)],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{B} {Rest} : Target J/resonator gains [+",
            tap_cost=True,
            will_cost=WillCost(darkness=1),
            effects=[EffectBuilder.buff(0, -200, EffectDuration.UNTIL_END_OF_TURN)],
        ))




@ScriptRegistry.register("TAT-094")
class MagicStoneOfBlastingWaves(RulesCardScript):
    """
    Magic Stone of Blasting Waves
    Continuous : Treat this card as wind magic stone and fire magic stone.
    Activate{Rest} : Produce{G} or{R} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.WIND, Attribute.FIRE],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{G} or{R} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.WIND)],
        ))




@ScriptRegistry.register("TAT-095")
class MagicStoneOfDarkDepth(RulesCardScript):
    """
    Magic Stone of Dark Depth
    Continuous : Treat this card as darkness magic stone and water magic stone.
    Activate{Rest} : Produce{B} and{U} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.DARKNESS, Attribute.WATER],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{B} and{U} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.DARKNESS)],
        ))




@ScriptRegistry.register("TAT-096")
class MagicStoneOfGustingSkies(RulesCardScript):
    """
    Magic Stone of Gusting Skies
    Continuous : Treat this card as light magic stone and wind magic stone.
    Activate{Rest} : Produce{W} and{G} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.LIGHT, Attribute.WIND],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{W} and{G} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.LIGHT)],
        ))




@ScriptRegistry.register("TAT-097")
class MagicStoneOfLightVapors(RulesCardScript):
    """
    Magic Stone of Light Vapors
    Continuous : Treat this card as light magic stone and water magic stone.
    Activate{Rest} : Produce{W} and{U} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.LIGHT, Attribute.WATER],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{W} and{U} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.LIGHT)],
        ))




@ScriptRegistry.register("TAT-098")
class MagicStoneOfScorchedBales(RulesCardScript):
    """
    Magic Stone of Scorched Bales
    Continuous : Treat this card as darkness magic stone and fire magic stone.
    Activate{Rest} : Produce{B} and{R} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.DARKNESS, Attribute.FIRE],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{B} and{R} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.DARKNESS)],
        ))




@ScriptRegistry.register("TAT-099")
class MilestTheGhostlyFlameStone(RulesCardScript):
    """
    Milest, the Ghostly Flame Stone
    Activate{Rest} : Produce{R} .
    Activate{R} {Rest} : This turn, if target J/resonator would deal damage, it deals that much +200 instead.
    Continuous When you control two or more true magic stones with the same name, banish all but one of them.
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.FIRE],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{R} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.FIRE)],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{R} {Rest} : This turn, if target J/reso",
            tap_cost=True,
            will_cost=WillCost(fire=1),
            effects=[],
        ))




@ScriptRegistry.register("TAT-100")
class MoojdartTheFantasyStone(RulesCardScript):
    """
    Moojdart, the Fantasy Stone
    Activate{Rest} : Produce{U} .
    Activate{U} {Rest} : Target J/resonator loses all races and gains a race of your choice until end of turn.
    Continuous When you control two or more magic stones with the same name, banish all but one of them.
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.WATER],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{U} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.WATER)],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{U} {Rest} : Target J/resonator loses al",
            tap_cost=True,
            will_cost=WillCost(water=1),
            effects=[],
        ))




@ScriptRegistry.register("TAT-101")
class MagicStoneOfLight(RulesCardScript):
    """
    Magic Stone of Light
    Activate{Rest} : Produce{W} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.LIGHT],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{W} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.LIGHT)],
        ))




@ScriptRegistry.register("TAT-102")
class MagicStoneOfFlame(RulesCardScript):
    """
    Magic Stone of Flame
    Activate{Rest} : Produce{R} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.FIRE],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{R} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.FIRE)],
        ))




@ScriptRegistry.register("TAT-103")
class MagicStoneOfWater(RulesCardScript):
    """
    Magic Stone of Water
    Activate{Rest} : Produce{U} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.WATER],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{U} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.WATER)],
        ))




@ScriptRegistry.register("TAT-104")
class MagicStoneOfWind(RulesCardScript):
    """
    Magic Stone of Wind
    Activate{Rest} : Produce{G} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.WIND],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{G} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.WIND)],
        ))




@ScriptRegistry.register("TAT-105")
class MagicStoneOfDarkness(RulesCardScript):
    """
    Magic Stone of Darkness
    Activate{Rest} : Produce{B} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.DARKNESS],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{B} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.DARKNESS)],
        ))



