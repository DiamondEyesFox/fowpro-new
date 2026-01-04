"""
Auto-generated card scripts for MPR

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


@ScriptRegistry.register("MPR-001")
class IThePilot(RulesCardScript):
    """
    "I", the Pilot
    Awakening{W} {1} : Enter : Search your main deck for a card named " The Little Prince " and put it into your field. This triggers its Enter ability. Then shuffle your main deck.
    Enter : Rest target resonator your opponent controls.
    Continuous : When " The Little Prince " is put into a graveyard from your field, you gain 1000 life.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(light=1, generic=1)
        # Enhanced effect triggers when awakening cost is paid

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Rest target resonator your opponent cont",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.rest()],
            is_mandatory=True,
        ))

        # [Continuous] ability
        # Continuous effect with: GAIN_LIFE
        # When \" The Little Prince \" is put into a graveyard from your field, yo


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("MPR-002")
class AbelTheAvengerOfGods(RulesCardScript):
    """
    Abel, the Avenger of Gods
    Target Attack
    Incarnation{W} ,{W} (You may banish two light resonators rather than play this card's cost.)
    Awakening{W} {W} {2} : Enter : Destroy all other resonators.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Incarnation alternative cost
        self.register_alternative_cost(IncarnationCost(
            required_attributes=[Attribute.LIGHT, Attribute.LIGHT],
            banish_count=2,
        ))

        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(light=2, generic=2)
        # Enhanced effect triggers when awakening cost is paid

        # [Continuous] ability
        # Continuous effect with: DESTROY
        # Awakening{W} {W} {2} : Enter : Destroy all other resonators.


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING | KeywordAbility.INCARNATION | KeywordAbility.TARGET_ATTACK



@ScriptRegistry.register("MPR-003")
class AccedeTheLight(RulesCardScript):
    """
    Accede the Light
    When target resonator you control is put into a graveyard this turn, search your main deck for a resonator with the same total cost as that resonator and put it into your field. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: SEARCH
        # When target resonator you control is put into a graveyard this turn, s




@ScriptRegistry.register("MPR-004")
class ApostleOfParadise(RulesCardScript):
    """
    Apostle of Paradise
    Continuous : This card cannot be destroyed as long as you control " Abel, the Avenger of Gods ".
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.INDESTRUCTIBLE



@ScriptRegistry.register("MPR-005")
class BookOfGenesis(RulesCardScript):
    """
    Book of Genesis
    Continuous : At the beginning of your main phase, put a creation counter on this card. Then, if this card has six or less creation counters on it, search your main deck for a resonator with total cost equal to the number of creation counters on this card and put it into your field. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: ADD_COUNTER
        # At the beginning of your main phase, put a creation counter on this ca




@ScriptRegistry.register("MPR-006")
class GenesisCreation(RulesCardScript):
    """
    Genesis Creation
    Put up to one target Addition: Field and up to one target resonator from your graveyard into your field. Put up to one target magic stone from your graveyard into your magic stone area.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: PUT_INTO_FIELD
        # Put up to one target Addition: Field and up to one target resonator fr




@ScriptRegistry.register("MPR-007")
class HolyWarriorOfHope(RulesCardScript):
    """
    Holy Warrior of Hope
    """

    pass


@ScriptRegistry.register("MPR-008")
class JekyllTheOrder(RulesCardScript):
    """
    Jekyll, the Order
    Enter : You gain 200 life.
    Activate Pay{B} , banish this card: Search your main deck for a card named " Hyde, the Chaos " and put it into your field. This triggers its Enter ability. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="You gain 200 life.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.gain_life(200)],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{B} , banish this card: Search your m",
            will_cost=WillCost(darkness=1),
            effects=[],
        ))




@ScriptRegistry.register("MPR-009")
class MindReadingFox(RulesCardScript):
    """
    Mind Reading Fox
    Continuous : This card cannot be targeted by spells or abilities your opponent controls.
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("MPR-010")
class PandoraTheWeaverOfMyth(RulesCardScript):
    """
    Pandora, the Weaver of Myth
    J-Activate Pay{W} {W} {W} {W} {W} . If your life is 3000 or less, pay{W} {W} {W} {W} instead. If your life is 2000 or less, pay{W} {W} instead. If your life is 1000 or less, pay{0} instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            will_cost=WillCost(light=5),
            j_ruler_code="MPR-010J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} {W} {W} {W} {W} . If your life is",
            will_cost=WillCost(light=5),
            effects=[],
        ))




@ScriptRegistry.register("MPR-010J")
class GrimmiaTheSaviorOfMyth(RulesCardScript):
    """
    Grimmia, the Savior of Myth
    Whenever this card attacks >>> You may search your main deck for a Weapon addition that can be added to a J/resonator and put it into the field, added to this card. If you do, shuffle your deck.
    Activate Pay{W} : This card gains Swiftness and Target Attack until end of turn.
    Activate Pay{W} {W} , banish an addition added to this card: Rest up to two target J/resonators.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Attack trigger ability
        self.register_ability(AutomaticAbility(
            name="Whenever this card attacks >>> You may s",
            trigger_condition=TriggerCondition.DECLARES_ATTACK,
            effects=[],
            is_mandatory=False,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} : This card gains Swiftness and T",
            will_cost=WillCost(light=1),
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} {W} , banish an addition added to",
            will_cost=WillCost(light=2),
            effects=[],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.SWIFTNESS | KeywordAbility.TARGET_ATTACK



@ScriptRegistry.register("MPR-011")
class RagnarokTheDivineSwordOfSavior(RulesCardScript):
    """
    Ragnarok, the Divine Sword of Savior
    Continuous : Added J/resonator gains [+500/+500].
    Continuous : If a resonator dealt damage by added J/resonator would be put into a graveyard this turn, remove that resonator from the game and you gain life equal to its DEF instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=500,
            def_=500,
            name="Added J/resonator gains [+500/",
        ))

        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME
        # If a resonator dealt damage by added J/resonator would be put into a g




@ScriptRegistry.register("MPR-012")
class SaviorOfSplendor(RulesCardScript):
    """
    Savior of Splendor
    Remove target darkness resonator from the game.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME
        # Remove target darkness resonator from the game.




@ScriptRegistry.register("MPR-013")
class SealOfGrimmia(RulesCardScript):
    """
    Seal of Grimmia
    Continuous : Added resonator cannot attack
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.CANNOT_ATTACK



@ScriptRegistry.register("MPR-014")
class SignToTheFuture(RulesCardScript):
    """
    Sign to the Future
    Trigger Your opponent controls three or more resonators than you: Remove two target resonators from the game.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Your opponent controls three or more res",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.remove_from_game()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-015")
class SpeakerOfCreation(RulesCardScript):
    """
    Speaker of Creation
    Enter : Search your main deck for an Addition:Field , reveal it and put it into your hand. Then shuffle your main deck.
    Activate Pay{W} , banish this card: Destroy target Addition:Field .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Search your main deck for an Addition:Fi",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} , banish this card: Destroy targe",
            will_cost=WillCost(light=1),
            effects=[EffectBuilder.destroy()],
        ))




@ScriptRegistry.register("MPR-016")
class SweetRose(RulesCardScript):
    """
    Sweet Rose
    Continuous : Added resonator gains [+300/+300]. If it's a Prince, it gains [+600/+600] and Target Attack instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=300,
            def_=300,
            name="Added resonator gains [+300/+3",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.TARGET_ATTACK



@ScriptRegistry.register("MPR-017")
class TheLittlePrince(RulesCardScript):
    """
    The Little Prince
    Continuous : This card gains [+400/+400] for each different total cost among resonators you control that don't share this card's total cost.
    Enter : You gain 1000 life if your life is 1000 or less.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="You gain 1000 life if your life is 1000 ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.gain_life(1000)],
            is_mandatory=True,
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=400,
            def_=400,
            name="This card gains [+400/+400] fo",
        ))




@ScriptRegistry.register("MPR-018")
class WhiteSpirit(RulesCardScript):
    """
    White Spirit
    Enter : You gain 500 life.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="You gain 500 life.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.gain_life(500)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-019")
class AkashicRecordsOfEternalFlame(RulesCardScript):
    """
    Akashic Records of Eternal Flame
    Continuous : You may pay{2} less to play a card if a card with the same name is in your graveyard.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # You may pay{2} less to play a card if a card with the same name is in 




@ScriptRegistry.register("MPR-020")
class ApostleOfCain(RulesCardScript):
    """
    Apostle of Cain
    Enter : If your J-Ruler attacked this turn, this card gains Swiftness until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="If your J-Ruler attacked this turn, this",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.grant_keyword(KeywordAbility.SWIFTNESS)],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.SWIFTNESS



@ScriptRegistry.register("MPR-021")
class ApostleOfCreation(RulesCardScript):
    """
    Apostle of Creation
    J-Activate Pay{R} .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            will_cost=WillCost(fire=1),
            j_ruler_code="MPR-021J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{R} .",
            will_cost=WillCost(fire=1),
            effects=[],
        ))




@ScriptRegistry.register("MPR-021J")
class CainTheTraitorOfGods(RulesCardScript):
    """
    Cain, the Traitor of Gods
    First Strike
    Continuous : You cannot call magic stones. At the beginning of your main phase, put the top card of your magic stone deck into your magic stone area.
    Continuous : Cognate resonators you control gain [+200/+0].
    Activate Pay{R} : This card deals 200 damage to target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{R} : This card deals 200 damage to t",
            will_cost=WillCost(fire=1),
            effects=[EffectBuilder.deal_damage(200), EffectBuilder.deal_damage(200)],
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=0,
            name="Cognate resonators you control",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FIRST_STRIKE



@ScriptRegistry.register("MPR-022")
class BlackGoat(RulesCardScript):
    """
    Black Goat
    Activate Pay{R} , remove this card in your graveyard from the game. This card deals 200 damage to target player or resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{R} , remove this card in your gravey",
            will_cost=WillCost(fire=1),
            effects=[EffectBuilder.deal_damage(200), EffectBuilder.deal_damage(200), EffectBuilder.remove_from_game()],
        ))




@ScriptRegistry.register("MPR-023")
class BlazerTheEaterOfDimensions(RulesCardScript):
    """
    Blazer, the Eater of Dimensions
    You may play this card from the removed area.
    Swiftness (This card can attack and play its{Rest} abilities the same turn it enters a field.)
    Continuous : If a card would be put into a graveyard from anywhere, remove it from the game instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME
        # If a card would be put into a graveyard from anywhere, remove it from 


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.SWIFTNESS



@ScriptRegistry.register("MPR-024")
class BulletOfEnvy(RulesCardScript):
    """
    Bullet of Envy
    Continuous : Added J/resonator gains [+800/+800] if your life is less than your opponent's life.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=800,
            def_=800,
            name="Added J/resonator gains [+800/",
        ))




@ScriptRegistry.register("MPR-025")
class CainComplex(RulesCardScript):
    """
    Cain Complex
    Trigger While a resonator your opponent controls is attacking: Until end of turn, gain control of target resonator that didn't attack this turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="While a resonator your opponent controls",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.gain_control()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-026")
class CrimeAndPunishment(RulesCardScript):
    """
    Crime and Punishment
    This card deals X damage to target J/resonator, where X is the damage it dealt this turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE
        # This card deals X damage to target J/resonator, where X is the damage 




@ScriptRegistry.register("MPR-027")
class EdenTheCrimsonGarden(RulesCardScript):
    """
    Eden, the Crimson Garden
    Continuous : Players cannot gain life.
    Continuous : At the end of turn, this card deals 200 damage to each player.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE
        # At the end of turn, this card deals 200 damage to each player.




@ScriptRegistry.register("MPR-028")
class FortyThieves(RulesCardScript):
    """
    Forty Thieves
    Enter : Draw two cards, then discard two cards.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Draw two cards, then discard two cards.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.draw(2), EffectBuilder.discard(1)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-029")
class GlyphOfUnkill(RulesCardScript):
    """
    Glyph of Unkill
    Continuous : Destroy added resonator at the end of its controller's turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DESTROY
        # Destroy added resonator at the end of its controller\'s turn.




@ScriptRegistry.register("MPR-030")
class JabalTheGrandsireOfNomads(RulesCardScript):
    """
    Jabal, the Grandsire of Nomads
    Continuous : When this card attacks, if your J-Ruler attacked this turn, target resonator cannot block this turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Attack trigger ability
        self.register_ability(AutomaticAbility(
            name="When this card attacks, if your J-Ruler ",
            trigger_condition=TriggerCondition.DECLARES_ATTACK,
            effects=[],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.CANNOT_BLOCK



@ScriptRegistry.register("MPR-031")
class JubalTheGrandsireOfMusicians(RulesCardScript):
    """
    Jubal, the Grandsire of Musicians
    Continuous : When this card attacks, if your J-Ruler attacked this turn, this card deals 500 damage to target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Attack trigger ability
        self.register_ability(AutomaticAbility(
            name="When this card attacks, if your J-Ruler ",
            trigger_condition=TriggerCondition.DECLARES_ATTACK,
            effects=[EffectBuilder.deal_damage(500), EffectBuilder.deal_damage(500)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-032")
class ShubniggurathTheGoddessOfFertility(RulesCardScript):
    """
    Shub-Niggurath, the Goddess of Fertility
    Incarnation{R} ,{R} or{B} (You may banish one fire resonator and one fire or darkness resonator rather than pay this card's cost.)
    Enter : Search your main deck for a card named " Black Goat " and put it into your field. Then shuffle your main deck.
    Activate{Rest} , banish two other Cthulhu resonators: Put target Cthulhu non-spell card from your graveyard into your field.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Incarnation alternative cost
        self.register_alternative_cost(IncarnationCost(
            required_attributes=[Attribute.FIRE, Attribute.FIRE, Attribute.DARKNESS],
            banish_count=2,
        ))

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Search your main deck for a card named \"",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} , banish two other Cthulhu resona",
            tap_cost=True,
            effects=[EffectBuilder.put_into_field(from_zone="graveyard")],
        ))

        # [Continuous] ability
        # Continuous effect with: BANISH
        # Incarnation{R} ,{R} or{B} (You may banish one fire resonator and one f


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.INCARNATION



@ScriptRegistry.register("MPR-033")
class SpawnOfBlazer(RulesCardScript):
    """
    Spawn of Blazer
    Flying
    Activate Banish this card: Produce two wills in any combination of attributes. Spend this will only to play Dragons.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish this card: Produce two wills in a",
            effects=[],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING



@ScriptRegistry.register("MPR-034")
class SplitHeavenAndEarth(RulesCardScript):
    """
    Split Heaven and Earth
    This card deals 300 damage to each player for each special magic stone that he or she controls.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE
        # This card deals 300 damage to each player for each special magic stone




@ScriptRegistry.register("MPR-035")
class TheFirstLie(RulesCardScript):
    """
    The First Lie
    Each player chooses a number secretly. Then those numbers are revealed. Each player with the highest number draws three cards and loses 100 life multiplied by the number he or she chose.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REVEAL
        # Each player chooses a number secretly. Then those numbers are revealed




@ScriptRegistry.register("MPR-036")
class TheHoundOfTindalos(RulesCardScript):
    """
    The Hound of Tindalos
    Continuous : This card gains [+200/+200] for each card named " The Hound of Tindalos " in your graveyard.
    Continuous : When this card is put into a graveyard from your field, you may pay{R} . If you do, search your main deck for a card named " The Hound of Tindalos " and put it into your field rested. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="This card gains [+200/+200] fo",
        ))

        # Triggered ability (RESTED)
        self.register_ability(AutomaticAbility(
            name="When this card is put into a graveyard f",
            trigger_condition=TriggerCondition.RESTED,
            effects=[],
            is_mandatory=False,
        ))




@ScriptRegistry.register("MPR-037")
class ApollosphereTheMoonLance(RulesCardScript):
    """
    Apollosphere, the Moon Lance
    Continuous : Added J/resonator gains [+400/+0].
    Continuous : You may banish this card rather than pay the cost of a water Spell:Chant-Instant .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=400,
            def_=0,
            name="Added J/resonator gains [+400/",
        ))




@ScriptRegistry.register("MPR-038")
class CampanellaTheMilkyWayMoon(RulesCardScript):
    """
    Campanella, the Milky Way Moon
    Enter : Search your main deck for a water Moon card and put it into your field. Then shuffle your main deck.
    Continuous : This card gains [+200/+200] as long as you control a Moon.
    Continuous : When a resonator is put into a graveyard from your field, you may banish this card. If you do, put that resonator from its owner's graveyard into his or her hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Search your main deck for a water Moon c",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="This card gains [+200/+200] as",
        ))

        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="When a resonator is put into a graveyard",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[],
            is_mandatory=False,
        ))




@ScriptRegistry.register("MPR-039")
class DarkShiningSwordsman(RulesCardScript):
    """
    Dark Shining Swordsman
    Activate Pay{M} {M} : Target resonator's printed ATK becomes 0 until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{M} {M} : Target resonator\'s printed ",
            will_cost=WillCost(moon=2),
            effects=[],
        ))




@ScriptRegistry.register("MPR-040")
class ElixirOfImmortality(RulesCardScript):
    """
    Elixir of Immortality
    Continuous : Prevent all battle damage that would be dealt to or dealt by added resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: PREVENT_DAMAGE
        # Prevent all battle damage that would be dealt to or dealt by added res




@ScriptRegistry.register("MPR-041")
class EtnaTheSnowQueen(RulesCardScript):
    """
    Etna, the Snow Queen
    Awakening{X} : Enter : Rest X target resonators. They cannot recover as long as this card is on field.
    Continuous : Whenever this card deals damage to your opponent, he or she discards a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(x_cost=True)
        # Enhanced effect triggers when awakening cost is paid

        # Triggered ability (DEALS_DAMAGE)
        self.register_ability(AutomaticAbility(
            name="Whenever this card deals damage to your ",
            trigger_condition=TriggerCondition.DEALS_DAMAGE,
            effects=[EffectBuilder.discard(1)],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("MPR-042")
class FallenComet(RulesCardScript):
    """
    Fallen Comet
    Return all rested resonators to their owners' hand. Then rest all resonators your opponent controls.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND
        # Return all rested resonators to their owners\' hand. Then rest all reso




@ScriptRegistry.register("MPR-043")
class GlimpseOfKaguya(RulesCardScript):
    """
    Glimpse of Kaguya
    Cancel target Activate ability. Draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DRAW
        # Cancel target Activate ability. Draw a card.




@ScriptRegistry.register("MPR-044")
class JoyfulBirdcatcher(RulesCardScript):
    """
    Joyful Bird-Catcher
    Activate Pay{U} ,{Rest} : Search your main deck for a Bird resonator, reveal it and put it into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{U} ,{Rest} : Search your main deck f",
            tap_cost=True,
            will_cost=WillCost(water=1),
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
        ))




@ScriptRegistry.register("MPR-045")
class KaiTheFrozenHeart(RulesCardScript):
    """
    Kai, the Frozen Heart
    Enter : Put three frozen counters on this card.
    Continuous : This card cannot attack or block as long as it has a frozen counter on it.
    Continuous : Whenever a resonator is put into a graveyard from your field, remove a frozen counter from this card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Put three frozen counters on this card.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="Whenever a resonator is put into a grave",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[EffectBuilder.remove_counter("frozen")],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.CANNOT_ATTACK



@ScriptRegistry.register("MPR-046")
class MoonPrincessOfStellarWars(RulesCardScript):
    """
    Moon Princess of Stellar Wars
    J-Activate Pay{2} {X} . Spend only{M} will on X.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            will_cost=WillCost(generic=2),
            j_ruler_code="MPR-046J",
        ))

        # Activated ability with X cost
        self.register_ability(ActivateAbility(
            name="Pay{2} {X} . Spend only{M} will on X.",
            x_cost=True,
            generic_cost=2,
            effects=[],
            uses_x=True,  # Effect uses X value from cost
        ))




@ScriptRegistry.register("MPR-046J")
class KaguyaTheImmortalPrincess(RulesCardScript):
    """
    Kaguya, the Immortal Princess
    Flying Imperishable
    Enter : Search your main deck for X Treasury Item cards and put them into your field.
    Continuous : This card gains [+200/+0] for each Treasury Item you control.
    Activate Banish three Treasury Items: Gain control of target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Search your main deck for X Treasury Ite",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish three Treasury Items: Gain contro",
            effects=[EffectBuilder.gain_control()],
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=0,
            name="This card gains [+200/+0] for ",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.IMPERISHABLE



@ScriptRegistry.register("MPR-047")
class MoonglowBird(RulesCardScript):
    """
    Moonglow Bird
    Continuous : This card gains [+400/+400] as long as you control a Moon.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=400,
            def_=400,
            name="This card gains [+400/+400] as",
        ))




@ScriptRegistry.register("MPR-048")
class PilotOfUniverse(RulesCardScript):
    """
    Pilot of Universe
    Activate Pay{M} : This card gains Flying until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{M} : This card gains Flying until en",
            will_cost=WillCost(moon=1),
            effects=[EffectBuilder.grant_keyword(KeywordAbility.FLYING)],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING



@ScriptRegistry.register("MPR-049")
class ShootingStar(RulesCardScript):
    """
    Shooting Star
    Change the target of target normal spell with a single target.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: GRANT_ABILITY
        # Change the target of target normal spell with a single target.




@ScriptRegistry.register("MPR-050")
class TheMilkyWay(RulesCardScript):
    """
    The Milky Way
    Enter : Draw a card.
    Continuous : Resonators your opponent controls cannot be targeted by spells or abilities.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Draw a card.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.draw(1)],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("MPR-051")
class TotalEclipse(RulesCardScript):
    """
    Total Eclipse
    Trigger While you control a Moon: Non-Wererabbit resonators gain [-500/0] and Wererabbit resonators gain [+500/0] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="While you control a Moon: Non-Wererabbit",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.buff(-500, 0, EffectDuration.UNTIL_END_OF_TURN)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-052")
class TsukuyomiTheMoonCity(RulesCardScript):
    """
    Tsukuyomi, the Moon City
    Activate Pay{1} ,{Rest} : Produce{M} .
    Activate Pay{1} , put this card on the bottom of your main deck: Target resonator you control gains Flying until end of turn. Draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{1} ,{Rest} : Produce{M} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.MOON)],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{1} , put this card on the bottom of ",
            effects=[EffectBuilder.draw(1), EffectBuilder.grant_keyword(KeywordAbility.FLYING)],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING



@ScriptRegistry.register("MPR-053")
class YangMageOfDecrescent(RulesCardScript):
    """
    Yang Mage of Decrescent
    Flying
    Activate Pay{M} : This card gains [+400/+0] until end of turn. Play this ability only once per turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{M} : This card gains [+400/+0] until",
            will_cost=WillCost(moon=1),
            effects=[EffectBuilder.buff(400, 0, EffectDuration.UNTIL_END_OF_TURN)],
            once_per_turn=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING



@ScriptRegistry.register("MPR-054")
class YinMageOfIncrescent(RulesCardScript):
    """
    Yin Mage of Increscent
    Flying
    Activate Pay{M} : This card gains [+0/+400] until end of turn. Play this ability only once per turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{M} : This card gains [+0/+400] until",
            will_cost=WillCost(moon=1),
            effects=[EffectBuilder.buff(0, 400, EffectDuration.UNTIL_END_OF_TURN)],
            once_per_turn=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING



@ScriptRegistry.register("MPR-055")
class AladdinsLamp(RulesCardScript):
    """
    Aladdin's Lamp
    Continuous : At the beginning of your main phase, you may reveal your hand. If you have no Spirit resonators in your hand, search your main deck for a Spirit resonator, reveal it and put it into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND, SEARCH
        # At the beginning of your main phase, you may reveal your hand. If you 




@ScriptRegistry.register("MPR-056")
class AliBabaTheEarnestWorker(RulesCardScript):
    """
    Ali Baba, The Earnest Worker
    Activate{Rest} : Draw a card if you have no cards in your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Draw a card if you have no card",
            tap_cost=True,
            effects=[EffectBuilder.draw(1)],
        ))




@ScriptRegistry.register("MPR-057")
class ArtOfSinbad(RulesCardScript):
    """
    Art of Sinbad
    Prevent the next damage that would be dealt by target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: PREVENT_DAMAGE
        # Prevent the next damage that would be dealt by target resonator.




@ScriptRegistry.register("MPR-058")
class BarrierField(RulesCardScript):
    """
    Barrier Field
    Continuous : If damage would be dealt to you by a normal spell, prevent 200 of it.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: PREVENT_DAMAGE
        # If damage would be dealt to you by a normal spell, prevent 200 of it.




@ScriptRegistry.register("MPR-059")
class DjinnTheSpiritOfLamp(RulesCardScript):
    """
    Djinn, the Spirit of Lamp
    Enter Remove up to three target resonator you control from the game. At the end of turn, put all resonators removed this way into their owner's field.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (TURN_END)
        self.register_ability(AutomaticAbility(
            name="Remove up to three target resonator you ",
            trigger_condition=TriggerCondition.TURN_END,
            effects=[EffectBuilder.remove_from_game()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-060")
class ExceedTheAncientMagic(RulesCardScript):
    """
    Exceed, the Ancient Magic
    Cancel target spell. If you control " Fiethsing, the Magus of Holy Wind ", draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DRAW, CANCEL
        # Cancel target spell. If you control \" Fiethsing, the Magus of Holy Win




@ScriptRegistry.register("MPR-061")
class FamiliarOfHolyWind(RulesCardScript):
    """
    Familiar of Holy Wind
    Enter : Draw a card.
    Activate Pay{G} , banish this card: This card deals 300 damage to target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Draw a card.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.draw(1)],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{G} , banish this card: This card dea",
            will_cost=WillCost(wind=1),
            effects=[EffectBuilder.deal_damage(300), EffectBuilder.deal_damage(300)],
        ))




@ScriptRegistry.register("MPR-062")
class FiethsingTheMagusOfHolyWind(RulesCardScript):
    """
    Fiethsing, the Magus of Holy Wind
    Quickcast (You may play this card anytime you can play a Spell:Chant-Instant .)
    Enter : Prevent all damage that would be dealt by target resonator until end of turn.
    Activate{Rest} : Produce one will of any attribute.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Prevent all damage that would be dealt b",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.prevent_all_damage()],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="(You may play this card anytime you can ",
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce one will of any attribu",
            tap_cost=True,
            effects=[EffectBuilder.produce_will_any()],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.QUICKCAST



@ScriptRegistry.register("MPR-063")
class FlyingCarpet(RulesCardScript):
    """
    Flying Carpet
    Enter : Draw a card.
    Continuous : Added resonator gains Flying
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Draw a card.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.draw(1)],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING



@ScriptRegistry.register("MPR-064")
class LiberatorOfWind(RulesCardScript):
    """
    Liberator of Wind
    At the beginning of the game, search your magic stone deck for a card.Then, shuffle the rest of your magic stone deck and put that card on top of it.
    J-Activate : Pay{1} {G} {G} .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{1} {G} {G} .",
            will_cost=WillCost(wind=2, generic=1),
            effects=[],
        ))




@ScriptRegistry.register("MPR-064J")
class ScheherazadeTheTellerOf1001Stories(RulesCardScript):
    """
    Scheherazade, the Teller of 1001 Stories
    Enter : Search your main deck, for a card and put it into your hand. The shuffle your main deck.
    Activate{Rest} : Draw two cards if you have no cards in your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Search your main deck, for a card and pu",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Draw two cards if you have no c",
            tap_cost=True,
            effects=[EffectBuilder.draw(2)],
        ))




@ScriptRegistry.register("MPR-065")
class MorgianaTheWiseServant(RulesCardScript):
    """
    Morgiana, the Wise Servant
    Continuous If you would draw a card in a phase other than draw phase, you may look at the top three cards of your main deck, put one of them into your hand and the rest on the bottom of your main deck in any order instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DRAW, RETURN_TO_HAND
        # If you would draw a card in a phase other than draw phase, you may loo




@ScriptRegistry.register("MPR-066")
class OpenSesame(RulesCardScript):
    """
    Open Sesame
    Trigger While you control "Ali Baba, the Earnest Worker": Search your main deck for up to two resonators, reveal them and put them into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="While you control \"Ali Baba, the Earnest",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-067")
class Rukh(RulesCardScript):
    """
    Rukh
    Flying
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING



@ScriptRegistry.register("MPR-068")
class SinbadTheWindriderMerchant(RulesCardScript):
    """
    Sinbad, the Windrider Merchant
    Continuous : Addition:Resonator cards in your hand gain Quickcast .
    Continuous : If you would draw a card in a phase other than draw phase, you may skip drawing it instead.
    When you skip drawing a card this way, choose one -
    this card deals 300 damage to target resonator; target resonator gains [+400/+400] until end of turn; or destroy target addition.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Modal ability: Choose 1
        modal_choices = [
            ("this card deals 300 damage to ", EffectBuilder.deal_damage(300)),
            ("target resonator gains [+400/+", EffectBuilder.buff(400, 400, EffectDuration.UNTIL_END_OF_TURN)),
            ("destroy target addition.", EffectBuilder.destroy()),
        ]
        self.register_ability(ModalAbility(
            name="Modal Choice",
            choices=modal_choices,
            choose_count=1,
        ))

        # [Continuous] ability
        # Continuous effect with: DRAW
        # If you would draw a card in a phase other than draw phase, you may ski

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=400,
            def_=400,
            name="this card deals 300 damage to ",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.QUICKCAST



@ScriptRegistry.register("MPR-069")
class StoriesToldIn1001Nights(RulesCardScript):
    """
    Stories Told in 1001 Nights
    Put target resonator on top of its owner's main deck. If your J/Ruler is " Liberator of Wind " or " Scheherazade, the Teller of 1001 Stories ", remove it from the game, then search its controller's main deck, graveyard and hand for all cards with the same name and remove them from the game instead. Then that player shuffles his or her main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME, PUT_ON_TOP_OF_DECK
        # Put target resonator on top of its owner\'s main deck. If your J/Ruler 




@ScriptRegistry.register("MPR-070")
class SurvivorOfHeavenCastle(RulesCardScript):
    """
    Survivor of Heaven Castle
    Continuous : Whenever this card blocks or is blocked, it gains [+300/+300] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (DECLARES_BLOCK)
        self.register_ability(AutomaticAbility(
            name="Whenever this card blocks or is blocked,",
            trigger_condition=TriggerCondition.DECLARES_BLOCK,
            effects=[EffectBuilder.buff(300, 300, EffectDuration.UNTIL_END_OF_TURN)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-071")
class WindDagger(RulesCardScript):
    """
    Wind Dagger
    Enter : Draw a card.
    Activate Pay{G} , banish this card: This card deals 300 damage to target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Draw a card.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.draw(1)],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{G} , banish this card: This card dea",
            will_cost=WillCost(wind=1),
            effects=[EffectBuilder.deal_damage(300), EffectBuilder.deal_damage(300)],
        ))




@ScriptRegistry.register("MPR-072")
class WisemanOfWinds(RulesCardScript):
    """
    Wiseman of Winds
    Enter : Banish this card if you don't control another Elf.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Banish this card if you don\'t control an",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.banish_self_conditional()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-073")
class AcolyteOfDarkness(RulesCardScript):
    """
    Acolyte of Darkness
    Continuous : When this card is banished by Incarnation , you may pay 400 life. If you do, draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When this card is banished by Incarnatio",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.draw(1)],
            is_mandatory=False,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.INCARNATION



@ScriptRegistry.register("MPR-074")
class AwakeningAtTheEnd(RulesCardScript):
    """
    Awakening at the End
    All resonators gain [-700/-700] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=-700,
            def_=-700,
            name="All resonators gain [-700/-700",
        ))




@ScriptRegistry.register("MPR-075")
class BindOfGravity(RulesCardScript):
    """
    Bind of Gravity
    Enter : Rest added resonator.
    Continuous : Added resonator cannot recover during recovery phase.
    Activate Pay{3} : Recover added resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Rest added resonator.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{3} : Recover added resonator.",
            effects=[],
        ))




@ScriptRegistry.register("MPR-076")
class BlackMiasma(RulesCardScript):
    """
    Black Miasma
    Target resonator gains [+300/+300] until end of turn if it's darkness. Otherwise, it gains [-300/-300] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=300,
            def_=300,
            name="Target resonator gains [+300/+",
        ))




@ScriptRegistry.register("MPR-077")
class BlackMoon(RulesCardScript):
    """
    Black Moon
    Continuous : At the beginning of your main phase, put target Cthulhu non-spell card from your graveyard into your field. It gains Swiftness until end of turn. If it would leave your field this turn, remove it from the game instead. At the end of turn, remove it from the game.
    Continuous : When this card it put into a graveyard from your field, you lose 1000 life.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME, GRANT_KEYWORD, PUT_INTO_FIELD
        # At the beginning of your main phase, put target Cthulhu non-spell card

        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="When this card it put into a graveyard f",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[EffectBuilder.lose_life(1000)],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.SWIFTNESS



@ScriptRegistry.register("MPR-078")
class ByakheeTheWingedLady(RulesCardScript):
    """
    Byakhee, the Winged Lady
    Flying
    Incarnation{B} {B} (You may banish two darkness resonators rather than pay this card's cost.)
    Activate{Rest} : Target resonator gains [+900/+900] and Flying until end of turn. When that resonator is destroyed this turn, banish this card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Incarnation alternative cost
        self.register_alternative_cost(IncarnationCost(
            required_attributes=[Attribute.DARKNESS, Attribute.DARKNESS],
            banish_count=2,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Target resonator gains [+900/+9",
            tap_cost=True,
            effects=[EffectBuilder.buff(900, 900, EffectDuration.UNTIL_END_OF_TURN)],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.INCARNATION



@ScriptRegistry.register("MPR-079")
class CallOfCthulhu(RulesCardScript):
    """
    Call of Cthulhu
    Trigger While you have five or more Cthulhu cards in your graveyard: Put target Cthulhu non-spell card from your graveyard into your field.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="While you have five or more Cthulhu card",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.put_into_field(from_zone="graveyard")],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-080")
class FiendOfDarkPyre(RulesCardScript):
    """
    Fiend of Dark Pyre
    J-Activate Pay{0} . Play this ability only if you put a Cthulhu into a field this turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            j_ruler_code="MPR-080J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{0} . Play this ability only if you p",
            effects=[],
        ))




@ScriptRegistry.register("MPR-080J")
class NyarlathotepTheFacelessGod(RulesCardScript):
    """
    Nyarlathotep, the Faceless God
    Enter Your opponent banishes a non-Cthulhu resonator.
    Continuous This card's ATK is equal to total ATK of Cthulhu resonators you control.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Your opponent banishes a non-Cthulhu res",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.banish(), EffectBuilder.opponent_banishes()],
            is_mandatory=True,
        ))

        # [Continuous] ability
        self.register_continuous_effect(ContinuousEffect(
            name="This card\'s ATK is equal to total ATK of",
            affects_self_only=True,
            # ATK/DEF calculated dynamically
        ))




@ScriptRegistry.register("MPR-081")
class HydeTheChaos(RulesCardScript):
    """
    Hyde, the Chaos
    Enter : Your opponent loses 200 life.
    Activate Pay{W} , banish this card: Search your main deck for a card named " Jekyll, the Order " and put it into your field. This triggers its Enter ability. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Your opponent loses 200 life.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} , banish this card: Search your m",
            will_cost=WillCost(light=1),
            effects=[],
        ))




@ScriptRegistry.register("MPR-082")
class KingInYellow(RulesCardScript):
    """
    King in Yellow
    Continuous : When this card is put into a graveyard from your field, search your main deck for a card named " King in Yellow ", reveal it and put it into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="When this card is put into a graveyard f",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-083")
class PhantasmOfVoid(RulesCardScript):
    """
    Phantasm of Void
    If you control " Zero, the Magus of Null ", you may pay{B} less to play this card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # If you control \" Zero, the Magus of Null \", you may pay{B} less to pla




@ScriptRegistry.register("MPR-084")
class Shantak(RulesCardScript):
    """
    Shantak
    Continuous : When this card is put into a graveyard from your field, you may discard a card. If you do, put this card from your graveyard into your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="When this card is put into a graveyard f",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.discard(1)],
            is_mandatory=False,
        ))




@ScriptRegistry.register("MPR-085")
class SheharyarTheDistrustKing(RulesCardScript):
    """
    Sheharyar, the Distrust King
    Continuous : At the end of your turn, if no resonator you control attacked this turn, banish another resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: BANISH, GRANT_ABILITY
        # At the end of your turn, if no resonator you control attacked this tur




@ScriptRegistry.register("MPR-086")
class ShiningTrapezohedron(RulesCardScript):
    """
    Shining Trapezohedron
    Continuous : Cthulhu you control gain [+200/+200].
    Activate Pay{B} , banish this card: Put the top five cards of your main deck into your graveyard.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{B} , banish this card: Put the top f",
            will_cost=WillCost(darkness=1),
            effects=[],
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="Cthulhu you control gain [+200",
        ))




@ScriptRegistry.register("MPR-087")
class VoidBlast(RulesCardScript):
    """
    Void Blast
    If you control " Zero, the Magus of Null ", you may pay{B} {1} less to play this card.
    Remove target resonator from the game.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # If you control \" Zero, the Magus of Null \", you may pay{B} {1} less to

        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME
        # Remove target resonator from the game.




@ScriptRegistry.register("MPR-088")
class YellowSign(RulesCardScript):
    """
    Yellow Sign
    Continuous : Added resonator gains [-300/-300]. At the end of turn, this card deals 300 damage to added resonator's controller.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=-300,
            def_=-300,
            name="Added resonator gains [-300/-3",
        ))




@ScriptRegistry.register("MPR-089")
class YogsothothTheDarkMyth(RulesCardScript):
    """
    Yog-Sothoth, the Dark Myth
    Incarnation{B} ,{R} or{B} ,{R} or{B} (You may banish a dark resonator and any combination of two fire or darkness resonators rather than pay this card's cost.)
    Pierce
    Enter : Destroy all resonators with total cost 2 or less.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Incarnation alternative cost
        self.register_alternative_cost(IncarnationCost(
            required_attributes=[Attribute.DARKNESS, Attribute.FIRE, Attribute.DARKNESS],
            banish_count=2,
        ))

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Destroy all resonators with total cost 2",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))

        # [Continuous] ability
        # Continuous effect with: BANISH
        # Incarnation{B} ,{R} or{B} ,{R} or{B} (You may banish a dark resonator 


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.PIERCE | KeywordAbility.INCARNATION



@ScriptRegistry.register("MPR-090")
class ZeroTheMagusOfNull(RulesCardScript):
    """
    Zero, the Magus of Null
    Quickcast (You may play this card anytime you can play a Spell:Chant-Instant .)
    Enter : Resonators your opponent controls gain [-200/-200] and lose Flying until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Resonators your opponent controls gain [",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.buff(-200, -200, EffectDuration.UNTIL_END_OF_TURN)],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="(You may play this card anytime you can ",
            effects=[],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.QUICKCAST



@ScriptRegistry.register("MPR-091")
class AliceTheGuardianOfDimensions(RulesCardScript):
    """
    Alice, the Guardian of Dimensions
    Flying
    Activate Pay{U} : Target resonator you control cannot be targeted by spells or abilities your opponent controls until end of turn.
    Activate Pay{W} ,{Rest} : Remove this card and target resonator from the game.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{U} : Target resonator you control ca",
            will_cost=WillCost(water=1),
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} ,{Rest} : Remove this card and ta",
            tap_cost=True,
            will_cost=WillCost(light=1),
            effects=[EffectBuilder.remove_from_game()],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.BARRIER



@ScriptRegistry.register("MPR-092")
class ApollobreakTheMoonBlast(RulesCardScript):
    """
    Apollobreak, the Moon Blast
    Put target resonator on top of its owner's main deck.
    Awakening{M} {M} : If your J/Ruler is " Moon Princess of Stellar Wars " or " Kaguya, the Immortal Princess ", put target resonator on the bottom of its owner's main deck and draw a card instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Awakening enhanced cost
        self.awakening_cost = AwakeningCost(moon=2)
        # Enhanced effect triggers when awakening cost is paid

        # [Continuous] ability
        # Continuous effect with: PUT_ON_TOP_OF_DECK
        # Put target resonator on top of its owner\'s main deck.

        # [Continuous] ability
        # Continuous effect with: DRAW
        # Awakening{M} {M} : If your J/Ruler is \" Moon Princess of Stellar Wars 


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.AWAKENING



@ScriptRegistry.register("MPR-093")
class FlameOfOuterWorld(RulesCardScript):
    """
    Flame of Outer World
    This card deals 800 damage to target J/resonator. Players cannot chase to this card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE
        # This card deals 800 damage to target J/resonator. Players cannot chase




@ScriptRegistry.register("MPR-094")
class GhertaTheTearOfPassion(RulesCardScript):
    """
    Gherta, the Tear of Passion
    Activate Remove a counter from a ruler or entity you control: This card gains Swiftness , Flying or Target Attack until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Remove a counter from a ruler or entity ",
            effects=[],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.SWIFTNESS | KeywordAbility.TARGET_ATTACK



@ScriptRegistry.register("MPR-095")
class GiovanniTheLonelyChild(RulesCardScript):
    """
    Giovanni, the Lonely Child
    Enter : If you don't control other resonators, search your main deck for a card named " Campanella, the Milky Way Moon ", reveal it and put it into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="If you don\'t control other resonators, s",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-096")
class HasturTheUnspeakable(RulesCardScript):
    """
    Hastur, the Unspeakable
    Incarnation{R} or{B} ,{R} or{B} (You may banish any combination of two fire or darkness resonators rather than pay this card's cost.)
    Enter : Destroy target resonator with no addition.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Incarnation alternative cost
        self.register_alternative_cost(IncarnationCost(
            required_attributes=[Attribute.FIRE],
            banish_count=1,
        ))

        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Destroy target resonator with no additio",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.INCARNATION



@ScriptRegistry.register("MPR-097")
class SethTheArbiter(RulesCardScript):
    """
    Seth, the Arbiter
    Continuous : Whenever your opponent discards a card, draw a card.
    Continuous : Whenever a resonator is put into a graveyard from your opponent's field, put target resonator from your graveyard into your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Whenever your opponent discards a card, ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.draw(1), EffectBuilder.discard(1)],
            is_mandatory=True,
        ))

        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="Whenever a resonator is put into a grave",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[EffectBuilder.return_from_graveyard()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("MPR-098")
class LittleRedThePureStone(RulesCardScript):
    """
    Little Red, the Pure Stone
    As this card comes into a magic stone area, choose an attribute.
    Activate{Rest} : Produce one will of the chosen attribute.
    Activate{Rest} : Target resonator that shares an attribute with the chosen attribute gains [+200/+200] until end of turn.
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
            name="{Rest} : Produce one will of the chosen ",
            tap_cost=True,
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Target resonator that shares an",
            tap_cost=True,
            effects=[EffectBuilder.buff(200, 200, EffectDuration.UNTIL_END_OF_TURN)],
        ))




@ScriptRegistry.register("MPR-099")
class MagicStoneOfMoonLight(RulesCardScript):
    """
    Magic Stone of Moon Light
    Activate{Rest} : Produce{M} .
    Activate{Rest} : Produce one will of any attribute that a magic stone you control could produce.
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.MOON],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{M} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.MOON)],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce one will of any attribu",
            tap_cost=True,
            effects=[EffectBuilder.produce_will_any()],
        ))




@ScriptRegistry.register("MPR-100")
class MagicStoneOfMoonShade(RulesCardScript):
    """
    Magic Stone of Moon Shade
    Activate{Rest} : Produce{M} .
    Activate{Rest} , pay 200 life: Produce{W} ,{R} ,{U} ,{G} or{B} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.MOON, Attribute.LIGHT],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{M} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.MOON)],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} , pay 200 life: Produce{W} ,{R} ,",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.LIGHT)],
        ))




@ScriptRegistry.register("MPR-101")
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




@ScriptRegistry.register("MPR-102")
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




@ScriptRegistry.register("MPR-103")
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




@ScriptRegistry.register("MPR-104")
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




@ScriptRegistry.register("MPR-105")
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



