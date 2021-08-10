import requests
import json

import random
from random import choice

import time, datetime

import discord, asyncio
from discord.ext import commands, tasks
from discord import Embed
from asyncio import sleep

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

name_map = {
    1: "Reload",
    2: "Defend",
    3: "Shoot",
    4: "Snipe"
}


red_scheme = [
    0xcd5c5c,
    0xf08080,
    0xe9967a,
    0xdc143c,
    0xff0000,
    0xb22222,
    0x8b0000
]

pink_scheme = [
    0xffc0cb,
    0xff69b4,
    0xff1493,
    0xc71585,
    0xdb7093
]

purple_scheme = [
    0xe6e6fa,
    0xd8bfd8,
    0xdda0dd,
    0xda70d6,
    0xff00ff,
    0xba55d3,
    0x9370db,
    0x663399,
    0x9932cc,
    0x8b008b,
    0x800080,
    0x4b0082,
    0x6a5acd,
    0x483d8b,
]

green_scheme = [
    0xadff2f,
    0x00ff00,
    0x32cd32,
    0x98fb98,
    0x00fa9a,
    0x3cb371,
    0x2e8b57,
    0x228b22,
    0x008000,
    0x006400,
    0x9acd32,
    0x6b8e23,
    0x808000,
    0x556b2f,
    0x66cdaa,
    0x8fbc8b,
    0x20b2aa,
    0x008b8b,
]


def colors_list():
    schemes = [red_scheme, pink_scheme, green_scheme, purple_scheme]
    random.shuffle(schemes)

    return [c for s in schemes for c in s]

### CLASS ###

class Player:
    """
    Player of a Gun Game
    --------------------
    ammo: How much ammunition the player holds
    user: Discord User object of the Player
    hp: Health Point (default setting 1)
    decision: The choice of the player during a round. After every round, reset to 0
    decision_recieved: Boolean of whether the player gave his or her choice to the Bot
    ffed: Boolean of whether the player FFed
    """

    def __init__(self, user, hp=1):
        self.ammo = 0
        self.user = user
        self.hp = hp
        self.decision = 0
        self.decision_recieved = False
        self.ffed = False
    
    def round_init(self):
        self.decision = 0
        self.decision_recieved = False

    def is_dead(self):
        return self.hp <= 0

    def reload(self):
        self.ammo += 1
    
    def shoot(self, bullets=1):
        self.ammo -= bullets

    def damaged(self, dmg=1):
        self.hp -= dmg

class Game:
    """
    One Gun Game
    --------------------
    host: Host Player
    opponent: Opponent Player
    round: Current # of Round
    ctx: Discord Context (given from the server !game message)
    id: Game ID in Game Manager
    manager: Game Manager
    """

    def __init__(self, host_user, opponent_user, ctx, game_id, manager, hp=1, snipeable=3):
        self.host = Player(host_user, hp=hp)
        self.opponent = Player(opponent_user, hp=hp)
        self.round = 0
        self.ctx = ctx
        self.id = game_id
        self.manager = manager
        self.colors = colors_list()

        self.snipeable = snipeable
    
    def get_color(self):
        try:
            color = self.colors[self.round]
            return color
        except IndexError:
            return 0xc7c2c5

    def appropriate_choices(self, player):
        if player.ammo >= self.snipeable:
            return 4
        elif player.ammo >= 1:
            return 3
        else:
            return 2

    def appropriate_msg(self, player):
        other = self.host
        if player == self.host:
            other = self.opponent

        if player.ammo >= self.snipeable:
            return "What will you pick? (Type the #)\n 1. Reload  2. Defend  3. Shoot  4. Snipe \n\n Your Ammo: {0}  |  Opponent Ammo: {1}".format(player.ammo, other.ammo)
        elif player.ammo >= 1:
            return "What will you pick? (Type the #)\n 1. Reload  2. Defend  3. Shoot \n\n Your Ammo: {0}  |  Opponent Ammo: {1}".format(player.ammo, other.ammo)
        else:
            return "What will you pick? (Type the #)\n 1. Reload  2. Defend \n\n Your Ammo: {0}  |  Opponent Ammo: {1}".format(player.ammo, other.ammo)

    async def host_msg(self):
        msg = self.appropriate_msg(self.host)
        choices = self.appropriate_choices(self.host)
        embed = Embed(title="Round {0}".format(str(self.round)), description=msg, color=0x3961AB)

        await self.host.user.send(embed=embed)

        @bot.event
        async def on_message(message):
            if self.host.decision_recieved: # If already got a response, don't react to new messages
                print("Host already recieved")
                return

            host_channel = message.channel
            if str(host_channel.type) == "private" and host_channel.recipient == self.host.user and message.author == self.host.user:  # Valid Source of Message
                print("Host MSG recieved")
                decision = message.content
                if len(decision) == 1 and "1" <= decision and decision <= str(choices): # Valid Message
                    decision = int(decision)
                    self.host.decision = decision
                    self.host.decision_recieved = True

                    if self.opponent.decision_recieved:
                        print("asdf")
                        self.interaction()
    
    async def opponent_msg(self):
        msg = self.appropriate_msg(self.opponent)
        choices = self.appropriate_choices(self.opponent)
        embed = Embed(title="Round {0}".format(str(self.round)), description=msg, color=0x3961AB)

        await self.opponent.user.send(embed=embed)

        @bot.event
        async def on_message(message):
            if self.opponent.decision_recieved: # If already got a response, don't react to new messages
                print("Opponent already recieved")
                return

            opponent_channel = message.channel
            if str(opponent_channel.type) == "private" and opponent_channel.recipient == self.opponent.user and message.author == self.opponent.user:  # Valid Source of Message
                print("Opponent MSG receieved")
                decision = message.content
                if len(decision) == 1 and "1" <= decision and decision <= str(choices): # Valid Message
                    decision = int(decision)
                    self.opponent.decision = decision
                    self.opponent.decision_recieved = True

                    if self.host.decision_recieved:
                        print("asdf")
                        self.interaction()

    async def send_dms(self):
        # Host
        msg = self.appropriate_msg(self.host)
        host_choices = self.appropriate_choices(self.host)
        embed = Embed(title="Round {0}".format(str(self.round)), description=msg, color=self.get_color())

        await self.host.user.send(embed=embed)

        # Opponent
        msg = self.appropriate_msg(self.opponent)
        opponent_choices = self.appropriate_choices(self.opponent)
        embed = Embed(title="Round {0}".format(str(self.round)), description=msg, color=self.get_color())

        await self.opponent.user.send(embed=embed)

        @bot.event
        async def on_message(message):
            channel = message.channel
            if str(channel.type) == "private" and channel.recipient == self.host.user and message.author == self.host.user:  # Valid Source of Message from Host
                print("Host MSG recieved")
                decision = message.content
                if decision.lower() == "ff" or decision.lower() == "forfeit":
                    self.host.decision_recieved = True
                    self.host.ffed = True
                    await self.ff_interaction(self.host)
                if self.host.decision_recieved: # If already got a response, don't react to new messages
                    print("Host already recieved")
                    return
                
                if len(decision) == 1 and "1" <= decision and decision <= str(host_choices): # Valid Message
                    decision = int(decision)
                    self.host.decision = decision
                    self.host.decision_recieved = True

                    if self.opponent.decision_recieved and not self.host.ffed:
                        print("asdf")
                        await self.interaction()
            elif str(channel.type) == "private" and channel.recipient == self.opponent.user and message.author == self.opponent.user:  # Valid Source of Message from Opponent
                print("Opponent MSG receieved")
                decision = message.content
                if decision.lower() == "ff" or decision.lower() == "forfeit":
                    self.opponent.decision_recieved = True
                    self.opponent.ffed = True
                    await self.ff_interaction(self.opponent)
                if self.opponent.decision_recieved: # If already got a response, don't react to new messages
                    print("Opponent already recieved")
                    return
                
                if len(decision) == 1 and "1" <= decision and decision <= str(opponent_choices): # Valid Message
                    decision = int(decision)
                    self.opponent.decision = decision
                    self.opponent.decision_recieved = True

                    if self.host.decision_recieved and not self.opponent.ffed:
                        print("asdf")
                        await self.interaction()
            
            await bot.process_commands(message)

    async def interaction(self):
        hd = self.host.decision
        od = self.opponent.decision

        if hd == 1:
            self.host.reload()
            if od == 1:
                self.opponent.reload()
            elif od == 2:
                pass
            elif od == 3:
                self.opponent.shoot()
                self.host.damaged()
            else:
                self.opponent.shoot(self.snipeable)
                self.host.damaged(self.snipeable)
        elif hd == 2:
            if od == 1:
                self.opponent.reload()
            elif od == 2:
                pass
            elif od == 3:
                self.opponent.shoot()
            else:
                self.opponent.shoot(self.snipeable)
                self.host.damaged(self.snipeable)
        elif hd == 3:
            self.host.shoot()
            if od == 1:
                self.opponent.reload()
                self.opponent.damaged()
            elif od == 2:
                pass
            elif od == 3:
                self.opponent.shoot()
                self.host.damaged()
                self.opponent.damaged()
            else:
                self.opponent.shoot(self.snipeable)
                self.host.damaged(self.snipeable)
                self.opponent.damaged()
        else:
            self.host.shoot(self.snipeable)
            self.opponent.damaged(self.snipeable)
            if od == 1:
                self.opponent.reload()
            elif od == 2:
                pass
            elif od == 3:
                self.opponent.shoot()
                self.host.damaged()
            else:
                self.opponent.shoot(self.snipeable)
                self.host.damaged(self.snipeable)

        await self.results_msg()
        await self.dead_interaction()

    async def results_msg(self):
        msg = "{0}: {1} \n\n {2}: {3}".format(self.host.user.mention, name_map[self.host.decision], self.opponent.user.mention, name_map[self.opponent.decision])
        embed=Embed(title="Round {0} Results".format(str(self.round)), description=msg, color = self.get_color())
        await self.ctx.send(embed=embed)
        await self.host.user.send(embed=embed)
        await self.opponent.user.send(embed=embed)
        

    async def dead_interaction(self):
        deads = self.check_dead()
        if deads == []: # Nobody died
            await self.new_round()
            return

        embed1 = Embed(title="You Won!", description="You have defeated your opponent", color=0x565656)
        embed2 = Embed(title="You Lost!", description="You have been shot, wounded, and defeated", color=0x565656)
        embed3 = Embed(title="Tie!", description="You have killed your opponent at the same time he or she did", color=0x565656)

        embed4 = Embed(title="We have a winner!", description="{0} won!".format(self.host.user.mention), color = 0x565656)
        embed5 = Embed(title="We have a winner!", description="{0} won!".format(self.opponent.user.mention), color = 0x565656)
        embed6 = Embed(title="Tie!", description="The two have killed each other at the same time", color = 0x565656)
        
        # Game has ended

        # Pop Game from Manager
        self.manager.games.pop(self.id)

        # Send Messages
        if deads == ["host"]:
            await self.host.user.send(embed=embed2)
            await self.opponent.user.send(embed=embed1)
            await self.ctx.send(embed=embed5)
        elif deads == ["opponent"]:
            await self.host.user.send(embed=embed1)
            await self.opponent.user.send(embed=embed2)
            await self.ctx.send(embed=embed4)
        else:
            await self.host.user.send(embed=embed3)
            await self.opponent.user.send(embed=embed3)
            await self.ctx.send(embed=embed6)

    def check_dead(self):
        if self.host.is_dead():
            if self.opponent.is_dead():
                return ["host", "opponent"]
            else:
                return ["host"]
        else:
            if self.opponent.is_dead():
                return ["opponent"]
            else:
                return []
    
    async def ff_interaction(self, player):
        other = self.host
        if player == self.host:
            other = self.opponent
        
        # Game has ended

        # Pop Game from Manager
        self.manager.games.pop(self.id)

        # Send Messages
        embed1 = Embed(title="You Won!", description="Your opponent FFed", color=0x565656)
        embed2 = Embed(title="You Lost!", description="You FFed", color=0x565656)
        embed3 = Embed(title="We have a winner!", description="{0} won from {1} forfeiting.".format(other.user.mention, player.user.mention), color = 0x565656)

        await other.user.send(embed=embed1)
        await player.user.send(embed=embed2)
        await self.ctx.send(embed=embed3)

    async def new_round(self):
        self.round += 1
        self.host.round_init()
        self.opponent.round_init()
        
        if self.round == 1:
            embed=Embed(title="Let the Gun Game Start!", description=self.host.user.mention + " vs " + self.opponent.user.mention, color = 0x565656)
            await self.ctx.send(embed=embed)

            ffembed=Embed(title="Let the Gun Game Start!", description="Type __FF__ if you want to forfeit!", color=0x565656)
            await self.host.user.send(embed=ffembed)
            await self.opponent.user.send(embed=ffembed)
        await self.send_dms()
        
                
class GameManager:
    """
    Manages Games and Checks if a Player is currently in a Game
    """

    def __init__(self):
        self.games = {}
        self.next_ind = 0

    def new_game(self, host, opponent, ctx, snipeable=3):
        self.next_ind += 1
        game = Game(host, opponent, ctx, self.next_ind, self, hp=1, snipeable=snipeable)
        self.games[self.next_ind] = game
        return game


    def is_playing(self, player):
        for game in self.games.values():
            if game.host.user == player or game.opponent.user == player:
                return True
        return False         


manager = GameManager()

### COMMANDS

@bot.command()
async def hello(ctx):
    # we do not want the bot to reply to itself
    if ctx.author == bot.user:
        return

    msg = 'Hello {0.author.mention}'.format(ctx)
    await ctx.send(msg)
    msg = 'Hello {0.author}'.format(ctx)
    await ctx.send(msg)

@bot.command(pass_context=True, aliases=['battle'])
async def game(ctx, mention, snipeable=3):
    print("!game done \n")

    # Retrieve Info of who the Opponent (the mentioned one) is
    opponent_id = None
    if '0' <= mention[2] and mention[2] <= '9':
        opponent_id = int(mention[2:-1])
    else:
        opponent_id = int(mention[3:-1])

    host = ctx.author
    opponent = ctx.guild.get_member(opponent_id)

    if host == opponent:
        embed=Embed(title="Cannot do so", description="You cannot fight yourself.", color=0xba8072)
        await ctx.send(embed=embed)
        return
    elif opponent.bot:
        embed=Embed(title="Cannot do so", description="You cannot fight a bot.", color=0xba8072)
        await ctx.send(embed=embed)
        return
    elif manager.is_playing(host):
        embed=Embed(title="Cannot do so", description="You must finish your own game first.", color=0xba8072)
        await ctx.send(embed=embed)
        return
    elif manager.is_playing(opponent):
        embed=Embed(title="Cannot do so", description="Your opponent is in a game.", color=0xba8072)
        await ctx.send(embed=embed)
        return
    
    # game = manager.new_game(host, opponent, ctx)
    #task = asyncio.create_task(game.new_round())
    asyncio.ensure_future(manager.new_game(host, opponent, ctx, snipeable).new_round())
    #await task
    


@bot.command(pass_context=True, aliases=['rules'])
async def rule(ctx):
    msg = """Gun Game is a 1v1 game that is done in multiple rounds. The objective of the game is to defeat your opponent before your opponent defeats you. If **A** kills **B** before **B** kills **A**, **A** wins. If **A** and **B** shoot and die at the same time, it will be a tie.

On each round, both players are given choices on what action to take. Regardless of whether a player has ammunition or not, he or she will always be able to pick among at least “Reload” or “Defend”. 

In the beginning of the game, since both players will start with no ammunition, both players will not have the option to “Shoot”. However, as players gain ammunition through “Reload”, they will also be given the option “Shoot”. 

When players have stacked up 3 ammunition or more, they are also given the option “Snipe”, which when selected will use 3 of their ammunition to execute a powerful attack.


**“Reload”** will give a player one more ammunition. However, there is a risk in this move: if the opposing player does “Shoot” or “Snipe”, the player who used “Reload” will die.

**“Defend”** will allow a player to defend himself from the opposing player’s “Shoot”. However, if your opponent does “Snipe”, the powerful attack will penetrate your “Defend”, and you will die. If the opposing player does something else, nothing will happen to the player.

**“Shoot”** will use one of the ammunition of a player to shoot a bullet towards the opposing player. If the opposing player does not “Defend”, the opposing player will die. However, if the opposing player uses an attack at the same time, both players will die and it will be a tie.

**“Snipe”** will use 3 of the ammunition of a player to launch a powerful attack towards the opposing player. The opposing player cannot use “Defend” to nullify this attack. However, if the opposing player uses an attack at the same time, both players will die and it will be a tie."""
    embed=Embed(title="Rules", description=msg, color=0x00ff00)
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    embed=Embed(title="Commands", description="\n**!game (mention)**: Do a 1v1 Gun Game with the mentioned user \n\n**!rules**: Get the rules of the Gun Game", color=0xcf8951)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

TOKEN = 'priv info'
bot.run(TOKEN)

