"""
Auto-generated card scripts for CMF

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


@ScriptRegistry.register("CMF-001")
class AesopThePrincesTutor(RulesCardScript):
    """
    Aesop, the Prince's Tutor
    Continuous : Each Fairy Tale you control cannot be targeted by spells or abilities your opponent controls.
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("CMF-002")
class BlindedPrince(RulesCardScript):
    """
    Blinded Prince
    Continuous : This card cannot attack or block.
    Activate Pay{0} : Thi card loses all abilities until end of turn. You cannot play this ability if you don't control " Rapunzel, the Long-Haired Princess ".
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{0} : Thi card loses all abilities un",
            effects=[EffectBuilder.add_restriction(), EffectBuilder.remove_all_abilities()],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.CANNOT_ATTACK



@ScriptRegistry.register("CMF-003")
class ClothesTailor(RulesCardScript):
    """
    Clothes Tailor
    Activate{Rest} : Move target Addition: Resonator you control onto another resonator
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Move target Addition: Resonator",
            tap_cost=True,
            effects=[],
        ))




@ScriptRegistry.register("CMF-004")
class DreamOfJuliet(RulesCardScript):
    """
    Dream of Juliet
    Choose one. If you control " Juliet, the Hope " and " Romeo, the Despair ", choose up to three instead - Destroy target addition: or draw a card; or remove target resonator from the game, then put it into its owner's field.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Modal ability: Choose 1
        modal_choices = [
            ("destroy target addition", EffectBuilder.destroy()),
            ("draw a card", EffectBuilder.draw(1)),
            ("remove target resonator from t", EffectBuilder.remove_from_game()),
        ]
        # Upgrade: you control " juliet, the hope " and " romeo, the 
        modal_upgrade_count = 3
        # TODO: Implement condition check
        self.register_ability(ModalAbility(
            name="Modal Choice",
            choices=modal_choices,
            choose_count=1,
        ))

        # [Continuous] ability
        # Continuous effect with: DRAW, DESTROY, REMOVE_FROM_GAME
        # Choose one. If you control \" Juliet, the Hope \" and \" Romeo, the Despa




@ScriptRegistry.register("CMF-005")
class GrimmTheFairyTalePrince(RulesCardScript):
    """
    Grimm, the Fairy Tale Prince
    Continuous : You may pay the attribute cost of Fairy Tale resonators with will of any attribute.
    Activate Pay{1} , discard a Fairy Tale resonator: Search your main deck for a Fairy Tale resonator, reveal it and put it into your hand. Then shuffle your main deck. This ability can be played only once per turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{1} , discard a Fairy Tale resonator:",
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
            once_per_turn=True,
        ))




@ScriptRegistry.register("CMF-006")
class HolyGrail(RulesCardScript):
    """
    Holy Grail
    Enter : Destroy target addition
    Activate{Rest} : Remove all damage that was dealt to target J-Ruler this turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Destroy target addition",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Remove all damage that was deal",
            tap_cost=True,
            effects=[],
        ))




@ScriptRegistry.register("CMF-007")
class JeweledBranchOfHorai(RulesCardScript):
    """
    Jeweled Branch of Horai
    Activate Pay{W} ,{Rest} : Rest up to two target fire or dark resonators.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} ,{Rest} : Rest up to two target f",
            tap_cost=True,
            will_cost=WillCost(light=1),
            effects=[],
        ))




@ScriptRegistry.register("CMF-008")
class JulietTheHope(RulesCardScript):
    """
    Juliet, the Hope
    Continuous : This card cannot be destroyed as long as you control " Romeo, the Despair ".
    Continuous : As long as you control " Romeo, the Despair ", each Nightmare resonator loses Nightmare and gains Fairy Tale.
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.INDESTRUCTIBLE



@ScriptRegistry.register("CMF-009")
class KingsServant(RulesCardScript):
    """
    King's Servant
    Enter : Put target Addition:Resonator from your graveyard into your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Put target Addition:Resonator from your ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_from_graveyard()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-010")
class KnightOfLoyalty(RulesCardScript):
    """
    Knight of Loyalty
    Activate Banish a card: target light J/resonator you control cannot be targeted by spells or abilites until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish a card: target light J/resonator ",
            effects=[],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("CMF-011")
class LightOfHope(RulesCardScript):
    """
    Light of Hope
    Trigger Your life is 2000 or lower: Put target attacking resonator on top of its owner's main deck. Resonators cannot attack until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Your life is 2000 or lower: Put target a",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.put_on_top_of_deck()],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.CANNOT_ATTACK



@ScriptRegistry.register("CMF-012")
class LightPalaceTheKingsCastle(RulesCardScript):
    """
    Light Palace, the King's Castle
    Continuous : Each Human you control gains [+200/+200].
    Activate Pay{W} , banish this card: Destroy target addition.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} , banish this card: Destroy targe",
            will_cost=WillCost(light=1),
            effects=[EffectBuilder.destroy()],
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="Each Human you control gains [",
        ))




@ScriptRegistry.register("CMF-013")
class PandoraGirlOfTheBox(RulesCardScript):
    """
    Pandora, Girl of the Box
    J-Activate Pay{W} {B} {3} .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            will_cost=WillCost(light=1, darkness=1, generic=3),
            j_ruler_code="CMF-013J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} {B} {3} .",
            will_cost=WillCost(light=1, darkness=1, generic=3),
            effects=[],
        ))




@ScriptRegistry.register("CMF-013J")
class PandoraOfLight(RulesCardScript):
    """
    Pandora of Light
    Enter : Destroy all resonators.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Destroy all resonators.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-014")
class RapunzelTheLonghairedPrincess(RulesCardScript):
    """
    Rapunzel, the Long-Haired Princess
    Continuous : This card doesn't recover during the recovery phase.
    Activate Rest a recovered resonator you control other than " Rapunzel, the Long-Haired Princess ": Recover this card.
    Activate{Rest} : Target resonator gains [+200/+0] and Flying until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Rest a recovered resonator you control o",
            tap_cost=True,
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Target resonator gains [+200/+0",
            tap_cost=True,
            effects=[EffectBuilder.buff(200, 0, EffectDuration.UNTIL_END_OF_TURN)],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING



@ScriptRegistry.register("CMF-015")
class ReturnToStories(RulesCardScript):
    """
    Return to Stories
    Remove target Nightmare of Fairy Tale resonator from the game.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REMOVE_FROM_GAME
        # Remove target Nightmare of Fairy Tale resonator from the game.




@ScriptRegistry.register("CMF-016")
class SilverStake(RulesCardScript):
    """
    Silver Stake
    Continuous : Resonator with this cannot attack or block if it's a Vampire. Otherwise, it gains [+400/+400], it cannot be targeted by Vampire spells or Vampire card's abilities and prevent any damage it would be dealt by Vampires.
    Activate Pay{W} : Return this card to its owner's hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} : Return this card to its owner\'s",
            will_cost=WillCost(light=1),
            effects=[EffectBuilder.return_to_hand()],
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=400,
            def_=400,
            name="Resonator with this cannot att",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER | KeywordAbility.CANNOT_ATTACK



@ScriptRegistry.register("CMF-017")
class TellAFairyTale(RulesCardScript):
    """
    Tell a Fairy Tale
    Search your main deck for a Fairy Tale resonator, reveal it and put it into your hand. If your Ruler is " Grimm, the Fairy Tale Prince ", you may put it into your field instead. This triggers its Enter ability. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND, SEARCH
        # Search your main deck for a Fairy Tale resonator, reveal it and put it




@ScriptRegistry.register("CMF-018")
class TheEmperorWithNewClothes(RulesCardScript):
    """
    The Emperor with New Clothes
    Enter : Destroy all Addition:Resonator your opponent controls.
    Continuous : Opponents cannot add Addition:Resonator .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Destroy all Addition:Resonator your oppo",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-019")
class TinkerBellTheSpirit(RulesCardScript):
    """
    Tinker Bell, the Spirit
    Continuous : This card gains [+200/+200] for each Fairy Tale you control
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="This card gains [+200/+200] fo",
        ))




@ScriptRegistry.register("CMF-020")
class BasketOfLittleRed(RulesCardScript):
    """
    Basket of Little Red
    Continuous : Resonator with this gains " Activate{Rest} : Search your main deck for a card with "Apple" in its name, reveal it and put into your hand. Then shuffle your main deck".
    Activate Pay{R} : Return this card to its owner's hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{R} : Return this card to its owner\'s",
            will_cost=WillCost(fire=1),
            effects=[EffectBuilder.return_to_hand()],
        ))

        # [Continuous] ability
        # Continuous effect with: SEARCH
        # Resonator with this gains \" Activate{Rest} : Search your main deck for




@ScriptRegistry.register("CMF-021")
class BloodyMoon(RulesCardScript):
    """
    Bloody Moon
    Continuous : Each Werewolf you control gains [+200/+200].
    Activate Banish this card: Destroy target special magic stone.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish this card: Destroy target special",
            effects=[EffectBuilder.destroy()],
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="Each Werewolf you control gain",
        ))




@ScriptRegistry.register("CMF-022")
class ClockworkAppleBomb(RulesCardScript):
    """
    Clockwork Apple Bomb
    Trigger If your Ruler is " Snow White " or your J-Ruler is "Bloody Snow White ": Destroy blocking resonator and blocked resonator. This card deals 500 damage to each controller of those resonators.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="If your Ruler is \" Snow White \" or your ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.deal_damage(500), EffectBuilder.deal_damage(500), EffectBuilder.destroy()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-023")
class CommanderOfWolves(RulesCardScript):
    """
    Commander of Wolves
    Enter : This card deals 400 damage to target resonator for each Werewolf you control.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="This card deals 400 damage to target res",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.deal_damage(400), EffectBuilder.deal_damage(400)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-024")
class GillesDeRaisTheGoldenDragon(RulesCardScript):
    """
    Gilles de Rais, the Golden Dragon
    Flying
    Swiftness (This card can attack and activate its{Rest} ability in a turn it comes into a field.)
    Continuous : This card gains [+200/+0] for each of your fire magic stone.
    Continuous : When this card is destroyed, you may banish three of your fire magic stones. If you do, put this card from its owner's graveyard into your field.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=0,
            name="This card gains [+200/+0] for ",
        ))

        # Triggered ability (DESTROYED)
        self.register_ability(AutomaticAbility(
            name="When this card is destroyed, you may ban",
            trigger_condition=TriggerCondition.DESTROYED,
            effects=[],
            is_mandatory=False,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.SWIFTNESS



@ScriptRegistry.register("CMF-025")
class GrannyByTheFireplace(RulesCardScript):
    """
    Granny by the Fireplace
    Continuous : Whenever a Werewolf comes into a field: swap ATK and DEF of this card until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Whenever a Werewolf comes into a field: ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-026")
class HunterInBlackForest(RulesCardScript):
    """
    Hunter in Black Forest
    Swiftness (This card can attack and activate its{Rest} ability in a turn it comes into a field.)
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.SWIFTNESS



@ScriptRegistry.register("CMF-027")
class LittleRedRidingHood(RulesCardScript):
    """
    Little Red Riding Hood
    J-Activate Pay{0} : You cannot play this ability if you haven't put any Moon into a field this turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            j_ruler_code="CMF-027J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{0} : You cannot play this ability if",
            effects=[EffectBuilder.add_restriction()],
        ))




@ScriptRegistry.register("CMF-027J")
class LittleRedTheWolfGirl(RulesCardScript):
    """
    Little Red, the Wolf Girl
    Swiftness (This card can attack and activate its{Rest} ability in a turn it comes into a field.)
    Enter : This card deals 800 damage to target resonator.
    Continuous : At end of turn, return this card to is Ruler side.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="This card deals 800 damage to target res",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.deal_damage(800), EffectBuilder.deal_damage(800)],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.SWIFTNESS



@ScriptRegistry.register("CMF-028")
class LoupgarouTheNewMoon(RulesCardScript):
    """
    Loup-Garou, the New Moon
    Continuous : Each Werewolf you control gains Swiftness .
    Continuous : Whenever a Werewolf you control attacks, this card deals 100 damage to an opponent. If you control a Moon, this card deals 200 damage instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Attack trigger ability
        self.register_ability(AutomaticAbility(
            name="Whenever a Werewolf you control attacks,",
            trigger_condition=TriggerCondition.DECLARES_ATTACK,
            effects=[EffectBuilder.deal_damage(100), EffectBuilder.deal_damage(100)],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.SWIFTNESS



@ScriptRegistry.register("CMF-029")
class MoonNightPouncer(RulesCardScript):
    """
    Moon Night Pouncer
    Continuous : Whenever you play a normal spell, this card gains First Strike and Swiftness until end of turn.
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FIRST_STRIKE | KeywordAbility.SWIFTNESS



@ScriptRegistry.register("CMF-030")
class MurderousSnowman(RulesCardScript):
    """
    Murderous Snowman
    Enter : Banish one magic stone you control
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Banish one magic stone you control",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.banish()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-031")
class PoisonApple(RulesCardScript):
    """
    Poison Apple
    Target resonator you control gains [+1000/+0] until end of turn. At the end of turn, destroy that resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=1000,
            def_=0,
            name="Target resonator you control g",
        ))




@ScriptRegistry.register("CMF-032")
class PurifyingFire(RulesCardScript):
    """
    Purifying Fire
    Choose one. If your Ruler is " Nameless Girl " or your J-Ruler is " Jeanne d'Arc, the Flame of Hatred ", choose up to two instead - This card deals 700 damage to target player, or this card deals 1000 damage to target Human
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Modal ability: Choose 1
        modal_choices = [
            ("if your ruler is \" nameless gi", EffectBuilder.deal_damage(700)),
        ]
        self.register_ability(ModalAbility(
            name="Modal Choice",
            choices=modal_choices,
            choose_count=1,
        ))

        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE
        # Choose one. If your Ruler is \" Nameless Girl \" or your J-Ruler is \" Je




@ScriptRegistry.register("CMF-033")
class RedHotIronShoes(RulesCardScript):
    """
    Red Hot Iron Shoes
    Continuous : Whenever resonator with this becomes rested, this card deals 500 damage to that resonator's controller.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (RESTED)
        self.register_ability(AutomaticAbility(
            name="Whenever resonator with this becomes res",
            trigger_condition=TriggerCondition.RESTED,
            effects=[EffectBuilder.deal_damage(500), EffectBuilder.deal_damage(500)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-034")
class RobeOfFirerat(RulesCardScript):
    """
    Robe of Fire-Rat
    Activate{Rest} : Prevent all damage from target fire resonator until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Prevent all damage from target ",
            tap_cost=True,
            effects=[EffectBuilder.prevent_all_damage()],
        ))




@ScriptRegistry.register("CMF-035")
class SevenDwarfs(RulesCardScript):
    """
    Seven Dwarfs
    Continuous : This card must attack if able.
    Continuous : As you choose a card to attack, you must choose this card if able.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_continuous_effect(ContinuousEffect(
            name="Must Attack",
            affects_self_only=True,
            # Forces this card to attack if able
        ))




@ScriptRegistry.register("CMF-036")
class SnowWhite(RulesCardScript):
    """
    Snow White
    J-Activate Pay{W} {R} {2} .
    J-Activate Pay{1} , discard " Poison Apple ".
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            will_cost=WillCost(light=1, fire=1, generic=2),
            j_ruler_code="CMF-036J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} {R} {2} .",
            will_cost=WillCost(light=1, fire=1, generic=2),
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{1} , discard \" Poison Apple \".",
            effects=[],
        ))




@ScriptRegistry.register("CMF-036J")
class BloodySnowWhite(RulesCardScript):
    """
    Bloody Snow White
    Target Attack (This card can attack against recovered J/resonator.)
    Activate{Rest} : Rest target J/resonator.
    Activate Pay{1} , discard " Poison Apple ": Destroy target resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Rest target J/resonator.",
            tap_cost=True,
            effects=[EffectBuilder.rest()],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{1} , discard \" Poison Apple \": Destr",
            effects=[EffectBuilder.destroy()],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.TARGET_ATTACK



@ScriptRegistry.register("CMF-037")
class WolfhauntedInBlackForest(RulesCardScript):
    """
    Wolf-Haunted in Black Forest
    Continuous : When this card is destroyed, if you don't control any Moon, this card deals 500 damage to you.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (DESTROYED)
        self.register_ability(AutomaticAbility(
            name="When this card is destroyed, if you don\'",
            trigger_condition=TriggerCondition.DESTROYED,
            effects=[EffectBuilder.deal_damage(500), EffectBuilder.deal_damage(500)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-038")
class Thunder(RulesCardScript):
    """
    Thunder
    This card deals 500 damage to target player or J/resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE
        # This card deals 500 damage to target player or J/resonator.




@ScriptRegistry.register("CMF-039")
class ArcherOfTheCrescentMoon(RulesCardScript):
    """
    Archer of the Crescent Moon
    Flying (This card cannot be blocked be resonators without Flying .)
    Continuous : This card gains [+300/+300] for each other Wererabbit you control.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=300,
            def_=300,
            name="This card gains [+300/+300] fo",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("CMF-040")
class CharlesVii(RulesCardScript):
    """
    Charles VII
    Activate Pay{1} , banish a Human resonator: Draw a card.
    Activate Pay{1} , banish a Human resonator: Return target resonator to its owner's hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{1} , banish a Human resonator: Draw ",
            effects=[EffectBuilder.draw(1)],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{1} , banish a Human resonator: Retur",
            effects=[EffectBuilder.return_to_hand()],
        ))




@ScriptRegistry.register("CMF-041")
class DeepOnes(RulesCardScript):
    """
    Deep Ones
    Continuous : This card gains[+200/+200] for each resonator in your graveyard
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_continuous_effect(ContinuousEffect(
            name="This card gains[+200/+200] for each reso",
            affects_self_only=True,
            # Scaling: +200/+200 for each matching card
            apply_func=lambda game, card: self._apply_scaling_buff(game, card, 200, 200),
        ))




@ScriptRegistry.register("CMF-042")
class FiveChallenges(RulesCardScript):
    """
    Five Challenges
    Trigger Anytime: Draw a card. If you control five or more Treasury Items, return all resonators your opponent controls to their owner's hands instead.
    Continuous : When you put a Treasury Item into a field, put this card from your graveyard into your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Anytime: Draw a card. If you control fiv",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.draw(1), EffectBuilder.return_to_hand()],
            is_mandatory=True,
        ))

        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND
        # When you put a Treasury Item into a field, put this card from your gra




@ScriptRegistry.register("CMF-043")
class HamelinsPiedPiper(RulesCardScript):
    """
    Hamelin's Pied Piper
    Enter : Rest target resonator your opponent controls. It doesn't recover during the recovery phase as long as this card is on a field.
    Continuous : Whenever this card attacks, rest target resonator your opponent controls. It doesn't recover during the recovery phase as long as this card is on a field.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Rest target resonator your opponent cont",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.rest()],
            is_mandatory=True,
        ))

        # Attack trigger ability
        self.register_ability(AutomaticAbility(
            name="Whenever this card attacks, rest target ",
            trigger_condition=TriggerCondition.DECLARES_ATTACK,
            effects=[EffectBuilder.rest()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-044")
class HeavenlyFeatheredRobe(RulesCardScript):
    """
    Heavenly Feathered Robe
    Gain control of added resonator as long as its total cost is 2 or less. Added resonator becomes water.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: GAIN_CONTROL
        # Gain control of added resonator as long as its total cost is 2 or less




@ScriptRegistry.register("CMF-045")
class Inquisition(RulesCardScript):
    """
    Inquisition
    Rest two recovered resonators you control. If your Ruler is " Nameless Girl " or your J-Ruler is " Jeanne d'Arc, the Flame of Hatred ", rest one recovered resonator you control instead. If you do, destroy target resonator. Its controller may copy this spell and may choose new targets for the copy.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DESTROY
        # Rest two recovered resonators you control. If your Ruler is \" Nameless




@ScriptRegistry.register("CMF-046")
class KnightOfTheNewMoon(RulesCardScript):
    """
    Knight of the New Moon
    Activate{Rest} : Draw a card, then discard a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Draw a card, then discard a car",
            tap_cost=True,
            effects=[EffectBuilder.draw(1), EffectBuilder.discard(1)],
        ))




@ScriptRegistry.register("CMF-047")
class NamelessGirl(RulesCardScript):
    """
    Nameless Girl
    J-Activate Pay{R} {U} {2} : If a Human is put into your graveyard from a field this turn, you may pay{0} to play this ability instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            will_cost=WillCost(fire=1, water=1, generic=2),
            j_ruler_code="CMF-047J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{R} {U} {2} : If a Human is put into ",
            will_cost=WillCost(fire=1, water=1, generic=2),
            effects=[],
        ))




@ScriptRegistry.register("CMF-047J")
class JeanneDarcTheFlameOfHatred(RulesCardScript):
    """
    Jeanne d'Arc, the Flame of Hatred
    Enter : Destroy all other Humans.
    Activate{Rest} : Prevent all damage from target Human resonator until end of turn.
    Activate Pay{R} {1} : This card deals 500 damage to target Human.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Destroy all other Humans.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Prevent all damage from target ",
            tap_cost=True,
            effects=[EffectBuilder.prevent_all_damage()],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{R} {1} : This card deals 500 damage ",
            will_cost=WillCost(fire=1, generic=1),
            effects=[EffectBuilder.deal_damage(500), EffectBuilder.deal_damage(500)],
        ))




@ScriptRegistry.register("CMF-048")
class OneinchBoy(RulesCardScript):
    """
    One-Inch Boy
    Continuous : Whenever this card deals damage to a resonator, destroy the resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (DEALS_DAMAGE)
        self.register_ability(AutomaticAbility(
            name="Whenever this card deals damage to a res",
            trigger_condition=TriggerCondition.DEALS_DAMAGE,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-049")
class PaleMoon(RulesCardScript):
    """
    Pale Moon
    Continuous Each Wererabbit you control gains [+200/+200].
    Activate Pay{U} , banish this card: Return target resonator to its owner's hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{U} , banish this card: Return target",
            will_cost=WillCost(water=1),
            effects=[EffectBuilder.return_to_hand()],
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="Each Wererabbit you control ga",
        ))




@ScriptRegistry.register("CMF-050")
class RabbitKick(RulesCardScript):
    """
    Rabbit Kick
    Choose one - Return target resonator to its owner's hand; or return up to two target resonators to their owner's hand if your control a Wererabbit resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Modal ability: Choose 1
        modal_choices = [
            ("return target resonator to its", EffectBuilder.return_to_hand()),
            ("return up to two target resona", EffectBuilder.return_to_hand()),
        ]
        self.register_ability(ModalAbility(
            name="Modal Choice",
            choices=modal_choices,
            choose_count=1,
        ))

        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND
        # Choose one - Return target resonator to its owner\'s hand; or return up




@ScriptRegistry.register("CMF-051")
class RatCatchersPipe(RulesCardScript):
    """
    Rat Catcher's Pipe
    Activate Pay{U} : Return this card to its owner's hand.
    Continuous : Resonator with this gains " Activate{Rest} : Rest target resonator."
    Continuous : If the resonator with this is " Hamelin's Pied Piper ", it gains " Activate Pay{U} : Recover this card."
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{U} : Return this card to its owner\'s",
            will_cost=WillCost(water=1),
            effects=[EffectBuilder.return_to_hand()],
        ))

        # [Continuous] ability
        # Continuous effect with: REST
        # Resonator with this gains \" Activate{Rest} : Rest target resonator.\"

        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # If the resonator with this is \" Hamelin\'s Pied Piper \", it gains \" Act




@ScriptRegistry.register("CMF-052")
class SeerOfTheBlueMoon(RulesCardScript):
    """
    Seer of the Blue Moon
    J-Activate Pay{0} : You cannot play this ability if you haven't put any Treasury Item into a field this turn.
    Continuous : You pay{1} to put cards into your chant-standby area rather than pay{2} .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            j_ruler_code="CMF-052J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{0} : You cannot play this ability if",
            effects=[EffectBuilder.add_restriction()],
        ))

        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # You pay{1} to put cards into your chant-standby area rather than pay{2




@ScriptRegistry.register("CMF-052J")
class KaguyaPrincessOfTheMoon(RulesCardScript):
    """
    Kaguya, Princess of the Moon
    Activate Pay{0} : Change the text of target Treasury Item you control by replacing all instances of one attribute with another one until end of turn.
    Activate Pay{U} {U} {1} : Search your main deck for a Treasury Item, reveal it and put it into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{0} : Change the text of target Treas",
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{U} {U} {1} : Search your main deck f",
            will_cost=WillCost(water=2, generic=1),
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
        ))




@ScriptRegistry.register("CMF-053")
class ServantOfKaguya(RulesCardScript):
    """
    Servant of Kaguya
    Flying
    Continuous : This card gains [+400/+400] for each Treasury Item you control.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=400,
            def_=400,
            name="This card gains [+400/+400] fo",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING



@ScriptRegistry.register("CMF-054")
class SquirmerOfTheDark(RulesCardScript):
    """
    Squirmer of the Dark
    Continuous : At the beginning of your main phase, put the top three cards from your magic stone deck into your graveyard. If you cannot put three cards into your graveyard this way, banish this card and you lose 1000 life. (If you have less than three cards in your magic stone deck left, put all cards from your magic stone deck into your graveyard instead.)
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: LOSE_LIFE
        # At the beginning of your main phase, put the top three cards from your




@ScriptRegistry.register("CMF-055")
class StoneBowlOfBuddha(RulesCardScript):
    """
    Stone Bowl of Buddha
    Activate{Rest} : Target resonator cannot be blocked by water resonators until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Target resonator cannot be bloc",
            tap_cost=True,
            effects=[],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("CMF-056")
class SwordsmanOfTheFullMoon(RulesCardScript):
    """
    Swordsman of the Full Moon
    Enter : Return target resonator to its owner's hand.
    Flying (This card cannot be blocked be resonators without Flying .)
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Return target resonator to its owner\'s h",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_to_hand()],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("CMF-057")
class VoiceOfTheFalseGod(RulesCardScript):
    """
    Voice of the False God
    Banish a resonator you control. If you do, draw two cards. If you banished a Human in this way, draw three cards instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DRAW, BANISH
        # Banish a resonator you control. If you do, draw two cards. If you bani




@ScriptRegistry.register("CMF-058")
class AbsoluteCakeZone(RulesCardScript):
    """
    Absolute Cake Zone
    Cancel target normal spell. If you control " Hansel " or " Gretel ", draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DRAW
        # Cancel target normal spell. If you control \" Hansel \" or \" Gretel \", d




@ScriptRegistry.register("CMF-059")
class AramisTheThreeMusketeers(RulesCardScript):
    """
    Aramis, the Three Musketeers
    Enter : Produce{G} for each Musketeer resonator you control.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Produce{G} for each Musketeer resonator ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.produce_will(Attribute.WIND)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-060")
class AthosTheThreeMusketeers(RulesCardScript):
    """
    Athos, the Three Musketeers
    Enter : Search your main deck for an Addition:Resonator , reveal it and put it into your hand. If your Ruler is " Puss in Boots " or your J-Ruler is " D'Artagnan, the Bayoneteer ", you may put that card on to this card instead. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Search your main deck for an Addition:Re",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
            is_mandatory=False,
        ))




@ScriptRegistry.register("CMF-061")
class ChristieTheWindTracker(RulesCardScript):
    """
    Christie, the Wind Tracker
    J-Activate Pay{G} {G} {2} : If your opponent controls a Vampire, Immortal of Werewolf resonator, you may pay{0} to play this ability instead.
    Activate{Rest} : Draw a card. You cannot play this ability if you don't have exactly five cards in your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            will_cost=WillCost(wind=2, generic=2),
            j_ruler_code="CMF-061J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{G} {G} {2} : If your opponent contro",
            will_cost=WillCost(wind=2, generic=2),
            effects=[],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Draw a card. You cannot play th",
            tap_cost=True,
            effects=[EffectBuilder.draw(1), EffectBuilder.add_restriction()],
        ))




@ScriptRegistry.register("CMF-061J")
class HelsingTheVampireHunter(RulesCardScript):
    """
    Helsing, the Vampire Hunter
    Enter : Target non-Human J/resonator loses all abilities until end of turn. At the end of turn, destroy it.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (TURN_END)
        self.register_ability(AutomaticAbility(
            name="Target non-Human J/resonator loses all a",
            trigger_condition=TriggerCondition.TURN_END,
            effects=[EffectBuilder.destroy(), EffectBuilder.remove_all_abilities()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-062")
class CottageOfCakes(RulesCardScript):
    """
    Cottage of Cakes
    Continuous : " Hansel " and " Gretel " you control cannot be targeted by spells or abilities you opponent controls.
    Activate Pay{G} ,{Rest} : Remove target resonator you control from the game.
    Activate Pay{G} ,{Rest} , banish this card: Return all resonators removed from the game by this card into your field.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{G} ,{Rest} : Remove target resonator",
            tap_cost=True,
            will_cost=WillCost(wind=1),
            effects=[EffectBuilder.remove_from_game()],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{G} ,{Rest} , banish this card: Retur",
            tap_cost=True,
            will_cost=WillCost(wind=1),
            effects=[],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("CMF-063")
class CowrieOfSwallows(RulesCardScript):
    """
    Cowrie of Swallows
    Activate{Rest} : Target wind resonator cannot be targeted by spells or abilities your opponent controls until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Target wind resonator cannot be",
            tap_cost=True,
            effects=[],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER



@ScriptRegistry.register("CMF-064")
class Crucifix(RulesCardScript):
    """
    Crucifix
    Continuous : Resonator with this gains [-1000/-1000] if its a Vampire. Otherwise it cannot be attacked or targeted by spells or abilities your opponent controls.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=-1000,
            def_=-1000,
            name="Resonator with this gains [-10",
        ))




@ScriptRegistry.register("CMF-065")
class ElvishBowman(RulesCardScript):
    """
    Elvish Bowman
    Activate{Rest} : Destroy target addition.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Destroy target addition.",
            tap_cost=True,
            effects=[EffectBuilder.destroy()],
        ))




@ScriptRegistry.register("CMF-066")
class ElvishExorcist(RulesCardScript):
    """
    Elvish Exorcist
    Enter : Destroy target Vampire resonator.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Destroy target Vampire resonator.",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-067")
class ElvishPriest(RulesCardScript):
    """
    Elvish Priest
    Activate{Rest} : Produce{G} .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{G} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.WIND)],
        ))




@ScriptRegistry.register("CMF-068")
class FinaTheSilverPlayer(RulesCardScript):
    """
    Fina, the Silver Player
    Continuous : If your Ruler is " Christie, the Wind Tracker " or your J-Ruler is " Helsing, the Vampire Hunter ", each resonator your opponent controls loses its symbol skills.
    Continuous : Each other Elf you control gains [+400/+400].
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=400,
            def_=400,
            name="Each other Elf you control gai",
        ))




@ScriptRegistry.register("CMF-069")
class Gretel(RulesCardScript):
    """
    Gretel
    Enter : Reveal the top card of your magic stone deck, if it's a wind magic stone, put it into your magic stone area.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Reveal the top card of your magic stone ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.reveal_top(), EffectBuilder.put_into_field(from_zone="hand")],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-070")
class Hansel(RulesCardScript):
    """
    Hansel
    Continuous : This card cannot be attacked as long as you control " Gretel ".
    Continuous : Whenever this card deals damage to an opponent, draw a card.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (DEALS_DAMAGE)
        self.register_ability(AutomaticAbility(
            name="Whenever this card deals damage to an op",
            trigger_condition=TriggerCondition.DEALS_DAMAGE,
            effects=[EffectBuilder.draw(1)],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-071")
class LawOfSilence(RulesCardScript):
    """
    Law of Silence
    Target player cannot play normal spells and summon spells until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: REMOVE_ABILITY
        # Target player cannot play normal spells and summon spells until end of




@ScriptRegistry.register("CMF-072")
class MusketeersBayonet(RulesCardScript):
    """
    Musketeer's Bayonet
    Continuous : Resonator with this gains [+400/+0]. If it's a Musketeer, it also gains First Strike and Pierce .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=400,
            def_=0,
            name="Resonator with this gains [+40",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.PIERCE | KeywordAbility.FIRST_STRIKE



@ScriptRegistry.register("CMF-073")
class PorthosTheThreeMusketeers(RulesCardScript):
    """
    Porthos, the Three Musketeers
    Pierce (If this card deals more battle damage than the lethal damage to J/resonator, it deals excess damage to your opponent.)
    """

    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.PIERCE



@ScriptRegistry.register("CMF-074")
class PussInBoots(RulesCardScript):
    """
    Puss in Boots
    J-Activate Pay{9} : If you control " Athos, the Three Musketeers ", you pay{3} less to play this ability. So does " Aramis, the Three Musketeers " and " Porthos, the Three Musketeers ".
    Continuous : You may pay{1} less to play Musketeer resonators.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            will_cost=WillCost(generic=9),
            j_ruler_code="CMF-074J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{9} : If you control \" Athos, the Thr",
            effects=[],
        ))

        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # You may pay{1} less to play Musketeer resonators.




@ScriptRegistry.register("CMF-074J")
class DartagnanTheBayoneteer(RulesCardScript):
    """
    D'Artagnan, the Bayoneteer
    Target Attack
    Pierce
    Continuous : Each Musketeer resonator you control gains [+400/+400].
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=400,
            def_=400,
            name="Each Musketeer resonator you c",
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.PIERCE | KeywordAbility.TARGET_ATTACK



@ScriptRegistry.register("CMF-075")
class SiegeWarfare(RulesCardScript):
    """
    Siege Warfare
    Trigger Your Ruler is " Puss in Boots " or your J-Ruler is " D'Artagnan, the Bayoneteer ", and you control " Athos, the Three Musketeers ", " Porthos, the Three Musketeers " and " Aramis, the Three Musketeers ": Destroy target resonator or J-Ruler.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Your Ruler is \" Puss in Boots \" or your ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-076")
class SilverBullet(RulesCardScript):
    """
    Silver Bullet
    If your Ruler is " Christie, the Wind Tracker " or your J-Ruler is " Helsing, the Vampire Hunter ", you may pay{1} less to play this card.
    Search your main deck for a wind resonator, reveal it and put it into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Complex continuous effect (needs manual implementation)
        # If your Ruler is \" Christie, the Wind Tracker \" or your J-Ruler is \" H

        # [Continuous] ability
        # Continuous effect with: RETURN_TO_HAND, SEARCH
        # Search your main deck for a wind resonator, reveal it and put it into 




@ScriptRegistry.register("CMF-077")
class AlucardTheDarkNoble(RulesCardScript):
    """
    Alucard, the Dark Noble
    J-Activate Pay{0} : You cannot play this ability if you don't control a Vampire resonator and a resonator your opponent controlled hasn't entered a graveyard this turn.
    Activate{Rest} : Target resonator gains [-0/-300] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            j_ruler_code="CMF-077J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{0} : You cannot play this ability if",
            effects=[EffectBuilder.add_restriction()],
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Target resonator gains [-0/-300",
            tap_cost=True,
            effects=[EffectBuilder.buff(0, -300, EffectDuration.UNTIL_END_OF_TURN)],
        ))




@ScriptRegistry.register("CMF-077J")
class DraculaTheDemonicOne(RulesCardScript):
    """
    Dracula, the Demonic One
    Flying (This card cannot be blocked by resonators without Flying .)
    Imperishable (If this card would be destroyed, move this card to your Ruler area as a Ruler without losing any abilities.)
    Continuous : Whenever a resonator your opponent controls is put into a graveyard, if it was dealt damage by this card this turn, put it into your field under your control. It gains Nightmare and Vampire in addition to its own race.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Triggered ability (PUT_INTO_GRAVEYARD)
        self.register_ability(AutomaticAbility(
            name="Whenever a resonator your opponent contr",
            trigger_condition=TriggerCondition.PUT_INTO_GRAVEYARD,
            effects=[],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.IMPERISHABLE | KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("CMF-078")
class AlvarezTheDemonCastle(RulesCardScript):
    """
    Alvarez, the Demon Castle
    Continuous : Each Vampire you control gains [+200/+200],
    Activate Pay{B} , banish this card: Put target Vampire resonator from your graveyard into your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{B} , banish this card: Put target Va",
            will_cost=WillCost(darkness=1),
            effects=[EffectBuilder.return_from_graveyard()],
        ))

        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=200,
            def_=200,
            name="Each Vampire you control gains",
        ))




@ScriptRegistry.register("CMF-079")
class BlackCoffinOfVampires(RulesCardScript):
    """
    Black Coffin of Vampires
    Continuous : Vampire resonator with this cannot be targeted by spells or abilities your opponent controls. Otherwise, it cannot attack or block.
    Activate Pay{B} : Return this card to its owner's hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{B} : Return this card to its owner\'s",
            will_cost=WillCost(darkness=1),
            effects=[EffectBuilder.return_to_hand()],
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.BARRIER | KeywordAbility.CANNOT_ATTACK



@ScriptRegistry.register("CMF-080")
class BloodsuckingImpulse(RulesCardScript):
    """
    Bloodsucking Impulse
    Target Vampire J/resonator you control deals damage equal to its ATK to another target J/resonator. You gain X life, where X is the damage dealt this divided by 2, rounded up to the nearest 100.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE
        # Target Vampire J/resonator you control deals damage equal to its ATK t




@ScriptRegistry.register("CMF-081")
class CarmillaTheQueenOfVampires(RulesCardScript):
    """
    Carmilla, the Queen of Vampires
    Enter Destroy target non-Vampire resonator. If your Ruler is " Alucard, the Dark Noble " or your J-Ruler is " Dracula, the Demonic One ", and the resonator destroyed this way is a Human, put it into your field under your control. It loses all races and becomes a Vampire.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Destroy target non-Vampire resonator. If",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.destroy()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-082")
class CinderellaTheAshenMaiden(RulesCardScript):
    """
    Cinderella, the Ashen Maiden
    Continuous : Whenever this card deals damage to your opponent, you may search your main deck for a Prince resonator, reveal it and put it into your hand. Then shuffle your main deck.
    Activate Banish a resonator: this card deals 200 damage to each resonator your opponent controls.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Banish a resonator: this card deals 200 ",
            effects=[EffectBuilder.deal_damage(200), EffectBuilder.deal_damage(200)],
        ))

        # Triggered ability (DEALS_DAMAGE)
        self.register_ability(AutomaticAbility(
            name="Whenever this card deals damage to your ",
            trigger_condition=TriggerCondition.DEALS_DAMAGE,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
            is_mandatory=False,
        ))




@ScriptRegistry.register("CMF-083")
class DeadmanPrince(RulesCardScript):
    """
    Deadman Prince
    Enter : Put target resonator from your graveyard into your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Put target resonator from your graveyard",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_from_graveyard()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-084")
class JewelsOnDragonsNeck(RulesCardScript):
    """
    Jewels on Dragon's Neck
    Activate Pay{B} ,{Rest} : Put target dark addition from your graveyard into your hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{B} ,{Rest} : Put target dark additio",
            tap_cost=True,
            will_cost=WillCost(darkness=1),
            effects=[EffectBuilder.return_from_graveyard()],
        ))




@ScriptRegistry.register("CMF-085")
class LoraTheBloodSpeaker(RulesCardScript):
    """
    Lora, the Blood Speaker
    Enter : Search your main deck for a Vampire resonator, reveal it and put it into your hand. Then shuffle your main deck.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Search your main deck for a Vampire reso",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.return_from_graveyard(), EffectBuilder.search(destination="hand")],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-086")
class MidnightBell(RulesCardScript):
    """
    Midnight Bell
    Trigger Total number of all resonators and all magic stones is twelve: Each resonator your opponent controls loses all abilities and becomes [0/200] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Total number of all resonators and all m",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.remove_all_abilities()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-087")
class PandoraGirlOfTheBox(RulesCardScript):
    """
    Pandora, Girl of the Box
    J-Activate Pay{W} {B} {3} .
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # Judgment ability - flip to J-Ruler
        self.register_ability(JudgmentAbility(
            name="Judgment",
            will_cost=WillCost(light=1, darkness=1, generic=3),
            j_ruler_code="CMF-087J",
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{W} {B} {3} .",
            will_cost=WillCost(light=1, darkness=1, generic=3),
            effects=[],
        ))




@ScriptRegistry.register("CMF-087J")
class PandoraOfDark(RulesCardScript):
    """
    Pandora of Dark
    Enter : Your opponent discards all cards from his or her hand.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Your opponent discards all cards from hi",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[EffectBuilder.discard_all()],
            is_mandatory=True,
        ))




@ScriptRegistry.register("CMF-088")
class PumpkinWitch(RulesCardScript):
    """
    Pumpkin Witch
    Enter Each resonator you control gains Flying and Swiftness until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="Each resonator you control gains Flying ",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.SWIFTNESS



@ScriptRegistry.register("CMF-089")
class ResurrectionOfVampire(RulesCardScript):
    """
    Resurrection of Vampire
    Put a Vampire resonator from your graveyard into your field. This triggers its Enter ability.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: PUT_INTO_FIELD
        # Put a Vampire resonator from your graveyard into your field. This trig




@ScriptRegistry.register("CMF-090")
class RomeoTheDespair(RulesCardScript):
    """
    Romeo, the Despair
    Continuous : When this card is put into your graveyard from a field, if you control " Juliet, the Hope ", you may pay{B} . If you do, put this card from your graveyard into your field.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Enter] ability
        self.register_ability(AutomaticAbility(
            name="When this card is put into your graveyar",
            trigger_condition=TriggerCondition.ENTER_FIELD,
            effects=[],
            is_mandatory=False,
        ))




@ScriptRegistry.register("CMF-091")
class ServantOfVampire(RulesCardScript):
    """
    Servant of Vampire
    Continuous : As your opponent plays spells or abilities targeting a Vampire you control, he or she must choose this card as one of its target if able.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: GRANT_ABILITY
        # As your opponent plays spells or abilities targeting a Vampire you con




@ScriptRegistry.register("CMF-092")
class SlipperOfCinderella(RulesCardScript):
    """
    Slipper of Cinderella
    Continuous : Resonator with this gains [+600/+600] if it's dark and its printed ATK and DEF is [400/400]. Otherwise, it gains [-400/-400].
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        self.register_ability(AbilityFactory.continuous_buff(
            atk=600,
            def_=600,
            name="Resonator with this gains [+60",
        ))




@ScriptRegistry.register("CMF-093")
class SpiralOfDespair(RulesCardScript):
    """
    Spiral of Despair
    Your opponent discards two cards. If your Ruler is " Pandora, Girl of the Box " or your J-Ruler is " Pandora of Light " or " Pandora of Dark ", he or she discards two cards at random instead.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DISCARD
        # Your opponent discards two cards. If your Ruler is \" Pandora, Girl of 




@ScriptRegistry.register("CMF-094")
class VampireBat(RulesCardScript):
    """
    Vampire Bat
    Flying (This card cannot be blocked by resonators without Flying .)
    Continuous : Whenever this card deals damage, you gain that much life.
    Activate Pay{B} : This card gains [+200/+0] until end of turn.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="Pay{B} : This card gains [+200/+0] until",
            will_cost=WillCost(darkness=1),
            effects=[EffectBuilder.buff(200, 0, EffectDuration.UNTIL_END_OF_TURN)],
        ))

        # Triggered ability (DEALS_DAMAGE)
        self.register_ability(AutomaticAbility(
            name="Whenever this card deals damage, you gai",
            trigger_condition=TriggerCondition.DEALS_DAMAGE,
            effects=[],
            is_mandatory=True,
        ))


    def get_keywords(self) -> KeywordAbility:
        return KeywordAbility.FLYING | KeywordAbility.UNBLOCKABLE



@ScriptRegistry.register("CMF-095")
class VampiresStaff(RulesCardScript):
    """
    Vampire's Staff
    Continuous At the beginning of your recovery phase, reveal the top card of your main deck. This card deals 100 damage to target player for each will symbol on the revealed card attribute cost and you gain that much life.
    """

    def initial_effect(self, game, card):
        """Register abilities when card is created."""
        # [Continuous] ability
        # Continuous effect with: DEAL_DAMAGE, DEAL_DAMAGE, REVEAL
        # At the beginning of your recovery phase, reveal the top card of your m




@ScriptRegistry.register("CMF-096")
class MagicStoneOfBlackSilence(RulesCardScript):
    """
    Magic Stone of Black Silence
    Continuous : Treat this card as wind magic stone and dark magic stone.
    Activate{Rest} : Produce{G} or{B} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.WIND, Attribute.DARKNESS],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{G} or{B} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.WIND)],
        ))




@ScriptRegistry.register("CMF-097")
class MagicStoneOfDeepWood(RulesCardScript):
    """
    Magic Stone of Deep Wood
    Continuous : Treat this card as wind magic stone and water magic stone.
    Activate{Rest} : Produce{G} or{U} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.WIND, Attribute.WATER],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{G} or{U} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.WIND)],
        ))




@ScriptRegistry.register("CMF-098")
class MagicStoneOfHearthsCore(RulesCardScript):
    """
    Magic Stone of Hearth's Core
    Continuous : Treat this card as fire magic stone and water magic stone.
    Activate{Rest} : Produce{R} or{U} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.FIRE, Attribute.WATER],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{R} or{U} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.FIRE)],
        ))




@ScriptRegistry.register("CMF-099")
class MagicStoneOfHeatRay(RulesCardScript):
    """
    Magic Stone of Heat Ray
    Continuous : Treat this card as light magic stone and fire magic stone.
    Activate{Rest} : Produce{W} or{R} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.LIGHT, Attribute.FIRE],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{W} or{R} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.LIGHT)],
        ))




@ScriptRegistry.register("CMF-100")
class MagicStoneOfHeavensRift(RulesCardScript):
    """
    Magic Stone of Heaven's Rift
    Continuous : Treat this card as light magic stone and dark magic stone.
    Activate{Rest} : Produce{W} or{B} .
    """

    def initial_effect(self, game, card):
        # Will ability: tap to produce will
        self.register_ability(AbilityFactory.will_ability(
            colors=[Attribute.LIGHT, Attribute.DARKNESS],
            tap=True
        ))

        # [Activate] ability
        self.register_ability(ActivateAbility(
            name="{Rest} : Produce{W} or{B} .",
            tap_cost=True,
            effects=[EffectBuilder.produce_will(Attribute.LIGHT)],
        ))




@ScriptRegistry.register("CMF-101")
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




@ScriptRegistry.register("CMF-102")
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




@ScriptRegistry.register("CMF-103")
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




@ScriptRegistry.register("CMF-104")
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




@ScriptRegistry.register("CMF-105")
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



