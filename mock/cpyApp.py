# Imports

import os
import discord
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from discord.ext import commands
from matplotlib.ticker import FixedLocator

# Package Parameter Alterations

plt.rcParams['savefig.dpi'] = 300 

# Bot Setup

description = "A bot which provides either COVID media coverage or "
description += "graphical/tabular COVID data upon request."
command_prefix = '!'
bot = commands.Bot(command_prefix=command_prefix, description=description)
# Rewrote predefined help function
bot.remove_command('help')

# Basic Bot Functionality

@bot.event
async def on_ready():
	'''Print bot credentials to CLI upon login'''
	print('Bot logged in: {user} - {uid}.'.format(user=bot.user.name, uid=bot.user.id))

@bot.command(name="help", 
	description="Returns all available commands.",
	aliases=['h'])
async def help(ctx, *args):
	'''Send help information as message upon request.'''
	helptext = "```\n"
	helptext += bot.user.name + ": " + bot.description + "\n\n"
	helptext += "Commands:\n"
	for command in bot.commands:
		if command.aliases:
			aliases_string = f", {command_prefix}".join(command.aliases)
			helptext += f"\t{command_prefix}{command} ({command_prefix}{aliases_string}) - {command.description}\n"
		else:
			helptext += f"\t{command_prefix}{command} - {command.description}\n"
	helptext += "```"
	await ctx.send(helptext)

@bot.command(name="info",
	description="Returns the source of COVID data used.",
	aliases=['i'])
async def get_info(ctx):
	source_message = "Source of data: " 
	source_message += "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"
	await ctx.send(source_message)

@bot.event
async def on_command_error(ctx, error):
	'''Provide an error message if a command is issued but not recognized.'''
	if isinstance(error, commands.errors.CommandNotFound):
		error_message = "I don't recognize that command. "
		error_message += "Use " + command_prefix + "help for a list of possible commands."
		await ctx.send(error_message)
	else:
		raise error

# Bot Commands
@bot.command(name="graph", 
	description="Returns a graph of active COVID cases over a specific month in a particular state.", 
	aliases=['g'])
async def graph(ctx, month, state):
	global month_info, month_links, covid_data
	months = list(month_info.keys())
	states = [state.lower() for state in list(covid_data['january'][0]['Province_State'])]
	if month.lower() in months and state.lower() in states:
		month_dfs = covid_data[month.lower()]
		data = [float(df[df['Province_State']==state.lower().title()]['Active'].values[0]) for df in month_dfs]
		discord_color_1 = "#2c2f33"
		discord_color_2 = "#ffffff"
		discord_color_3 = "#7289da"
		fig, ax = plt.subplots(facecolor=(discord_color_1))
		ax.plot(range(1, month_info[month.lower()] + 1), data, color=discord_color_3)
		ax.xaxis.set_major_locator(FixedLocator([2, 7, 14, 21, 28, 31]))
		ax.spines['right'].set_visible(False)
		ax.spines['top'].set_visible(False)
		ax.spines['left'].set_color(discord_color_2)
		ax.spines['bottom'].set_color(discord_color_2)
		ax.yaxis.set_ticks_position('left')
		ax.xaxis.set_ticks_position('bottom')
		ax.set_xlabel('Day', color=discord_color_2)
		ax.set_ylabel('# of Active Cases / Day', color=discord_color_2)
		ax.set_title(f'Active Cases / Day, {state.title()}, {month.title()} 2021', color=discord_color_2)
		ax.tick_params(labelcolor=discord_color_2)
		ax.tick_params(axis='x', colors=discord_color_2, labelcolor=discord_color_2)
		ax.tick_params(axis='y', colors=discord_color_2, labelcolor=discord_color_2)
		ax.set_facecolor(discord_color_1)
		fig.tight_layout()
		image = get_discord_image(plt, fig)
		await ctx.send(file=image)
	else:
		error_message = "Please supply a full month name and a full state name as arguments."
		await ctx.send(error_message)

# Helper Functions

def get_discord_image(plt, fig):
	temp_file = "temp.png"
	plt.savefig(temp_file, facecolor=fig.get_facecolor(), edgecolor='none')
	plt.close()
	image = discord.File(temp_file)
	os.remove(temp_file)
	return image

def get_month_links():
	root = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/"
	root += "csse_covid_19_data/csse_covid_19_daily_reports_us/"
	month_info = {"january":31, "february":28}
	'''
	"march":31, "april":30, "may":31, "june":30, "july":31, "august":31,
	"september":30, "october":31, "november":30, "december":31
	'''
	year = '2021'
	month_days = {k:[str(x).zfill(2) for x in range(1, v + 1)] for k, v in month_info.items()}
	month_numbers = {k:str(v).zfill(2) for k, v in zip(month_info.keys(), range(1, 13))}
	month_csvs = {k:[month_numbers[k] + '-' + x + '-' + year + '.csv' for x in month_days[k]] for k in month_info.keys()}
	month_links = {k:[root+csv for csv in v] for k,v in month_csvs.items()}
	return month_info, month_links

def get_covid_data():
	global month_info, month_links
	return {k:[pd.read_csv(x) for x in month_links[k]] for k in month_links.keys()}

# Driver Code
if __name__ == '__main__':
	month_info, month_links = get_month_links()
	print("Downloading COVID data...")
	covid_data = get_covid_data()
	print("COVID data downloaded!")
	key = 'DISCOVIR_KEY'
	bot.run(os.environ[key])
