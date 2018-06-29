import random
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import BARRACKS, COMMANDCENTER, SUPPLYDEPOT, MARINE, SCV, \
    REFINERY, FACTORY, HELLION


class MarineRushBot(sc2.BotAI):
    def __init__(self):
        self.iterations_per_minute = 165
        self.max_workers = 60

    async def on_step(self, iteration):
        self.iteration = iteration
        await self.distribute_workers()
        await self.build_workers()
        await self.build_supplydepot()
        await self.build_refinery()
        await self.expand()
        await self.build_offensive_buildings()
        await self.build_offensive_units()
        await self.attack()

    async def build_workers(self):
        if self.units(COMMANDCENTER).amount * 16 > self.units(SCV).amount:
            if self.units(SCV).amount < self.max_workers:
                for commandcenter in self.units(COMMANDCENTER).ready.noqueue:
                    if self.can_afford(SCV):
                        await self.do(commandcenter.train(SCV))

    async def build_supplydepot(self):
        if self.supply_left < 5 and not self.already_pending(SUPPLYDEPOT):
            commandcenter = self.units(COMMANDCENTER).ready
            if commandcenter.exists:
                if self.can_afford(SUPPLYDEPOT):
                    await self.build(SUPPLYDEPOT,
                                     near=commandcenter.random,
                                     max_distance=300)

    async def build_refinery(self):
        if self.units(REFINERY).ready.amount < 2:
            for commandcenter in self.units(COMMANDCENTER).ready:
                vaspenes = self.state.vespene_geyser.closer_than(15.0, commandcenter)
                for vaspene in vaspenes:
                    if not self.can_afford(REFINERY):
                        break
                    worker = self.select_build_worker(vaspene.position)
                    if worker is None:
                        break
                    if not self.units(REFINERY).closer_than(1.0, vaspene).exists:
                        await self.do(worker.build(REFINERY, vaspene))

    async def expand(self):
        if self.units(COMMANDCENTER).amount < 3 and self.can_afford(COMMANDCENTER):
            await self.expand_now()

    async def build_offensive_buildings(self):
        if self.units(COMMANDCENTER).ready.exists and self.units(SUPPLYDEPOT).ready.exists and self.units(BARRACKS).empty:
            if self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):
                await self.build(BARRACKS, near=self.units(COMMANDCENTER).first, max_distance=300)
        elif self.units(COMMANDCENTER).ready.exists and self.units(SUPPLYDEPOT).ready.exists:
            if self.units(BARRACKS).amount < ((self.iteration / self.iterations_per_minute) / 2):
                if self.can_afford(BARRACKS) and not self.already_pending(BARRACKS):
                    await self.build(BARRACKS, near=self.units(BARRACKS).random, max_distance=300)

        if self.units(BARRACKS).ready.exists:
            if self.units(FACTORY).amount < ((self.iteration / self.iterations_per_minute) / 2):
                if self.can_afford(FACTORY) and not self.already_pending(FACTORY):
                    await self.build(FACTORY, near=self.units(BARRACKS).random)

    async def build_offensive_units(self):
        for barrack in self.units(BARRACKS).ready.noqueue:
            if not self.units(MARINE).amount > self.units(HELLION).amount * 3:
                if self.can_afford(MARINE) and self.supply_left > 0:
                    await self.do(barrack.train(MARINE))

        for factory in self.units(FACTORY).ready.noqueue:
            if self.can_afford(HELLION) and self.supply_left > 0:
                await self.do(factory.train(HELLION))

    async def attack(self):
        for marine in self.units(MARINE).idle:
            if self.units(MARINE).ready.amount > 15:
                await self.do(marine.attack(self.known_enemy_structures.random_or(
                    self.enemy_start_locations[0]).position))
            elif len(self.known_enemy_units) > 0:
                await self.do(marine.attack(random.choice(self.known_enemy_units)))

        for hellion in self.units(HELLION).idle:
            if self.units(HELLION).ready.amount > 5:
                await self.do(hellion.attack(self.known_enemy_structures.random_or(
                    self.enemy_start_locations[0]).position))
            elif len(self.known_enemy_units) > 0:
                await self.do(hellion.attack(random.choice(self.known_enemy_units)))


if __name__ == '__main__':
    run_game(maps.get('AbyssalReefLE'), [
        Bot(Race.Terran, MarineRushBot()),
        Computer(Race.Terran, Difficulty.Medium)
        ], realtime=False)
