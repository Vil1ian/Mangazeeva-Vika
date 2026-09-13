import random

class Unit:
    bonus = 0
    verb = "атакует"
    weapon = ""

    def __init__(self, nickname, hp, power):
        self.nickname = nickname
        self._hp = hp
        self._power = power

    @property
    def hp(self):
        return self._hp

    def alive(self):
        return self._hp > 0

    def hit(self, opponent):
        dmg = random.randint(1, self._power) + self.bonus
        opponent.receive_hit(dmg)
        print(f"{self.nickname} {self.verb} {opponent.nickname} "
              f"{self.weapon} (урон {dmg}). HP {opponent.nickname}: {opponent.hp}")

    def receive_hit(self, dmg):
        self._hp = max(0, self._hp - dmg)

    def __str__(self):
        return f"{self.nickname} [{self.hp} HP]"


class Elf(Unit):
    bonus = 3
    verb = "бьёт из лука"

class Orc(Unit):
    bonus = 5
    verb = "обрушивает топор на"

class Human(Unit):
    bonus = 2
    verb = "кидает копьё в"

class Gnome(Unit):
    bonus = 1
    verb = "замахивается киркой на"


squad = [
    Elf("Арвен", 90, 16),
    Orc("Крушитель", 130, 15),
    Human("Оливер", 100, 14),
    Gnome("Грумми", 115, 11),
]

battle_round = 1
while sum(u.alive() for u in squad) > 1:
    print(f"\nСхватка {battle_round}")
    for unit in squad:
        if not unit.alive():
            continue
        targets = [u for u in squad if u.alive() and u is not unit]
        if not targets:
            break
        target = random.choice(targets)
        if target.alive():
            unit.hit(target)
    battle_round += 1

survivors = [u for u in squad if u.alive()]
if survivors:
    print(f"\nВыжил в бою: {survivors[0]}")
else:
    print("\nНикто не выжил.")