import discord
from discord.ext import commands
import nbtlib
import io
import logging
from discord import app_commands
import secret

logging.basicConfig(level=logging.INFO)

def map_data_version(data_version):
    mapping = {
        3463: "1.20",
        3465: "1.20.1",
        3578: "1.20.2",
        3698: "1.20.3",
        3700: "1.20.4",
        3837: "1.20.5",
        3839: "1.20.6",
        3953: "1.21",
        3955: "1.21.1",
        4080: "1.21.2",
        4082: "1.21.3",
        4189: "1.21.4",
        4325: "1.21.5",
    }
    lowest = min(mapping.keys())
    latest = max(mapping.keys())

    if data_version < lowest:
        return f"<1.20 ([unmapped data version: {data_version}](<https://minecraft.wiki/w/Data_version#List_of_data_versions>))"
    elif data_version > latest:
        return f">1.21.5 ([unmapped data version: {data_version}](<https://minecraft.wiki/w/Data_version#List_of_data_versions>))"
    elif data_version in mapping:
        return mapping[data_version]
    else:
        return f"Unknown ([data version: {data_version}](<https://minecraft.wiki/w/Data_version#List_of_data_versions>))"

def get_schematic_format(version):
    if version == 2:
        return "schem.2"
    elif version == 3:
        return "schem.3"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        # Sync commands globally
        synced = await bot.tree.sync()
        logging.info("commands synced")
    except Exception as e:
        logging.error(exc_info=e)
    logging.info(f"started {bot.user}")

@bot.tree.command(name="schem", description="Debug a .schem file")
async def schem(interaction: discord.Interaction, file: discord.Attachment):
    
    logging.info(f"{interaction.user} ran /schem {file.filename}")

    if not file.filename.endswith('.schem'):
        await interaction.response.send_message("Upload a .schem", ephemeral=True)
        return

    try:
        # read as nbt
        file_bytes = await file.read()
        logging.info(f"read {len(file_bytes)} bytes")
        file_buffer = io.BytesIO(file_bytes)
        nbt_file = nbtlib.load(file_buffer, gzipped=True)
        if hasattr(nbt_file, 'root'):
            root = nbt_file.root
        else:
            root = nbt_file

        if "Schematic" in root:
            # sponge3 (ithink)
            schematic_data = root["Schematic"]
            version = schematic_data.get("Version")
            data_version = schematic_data.get("DataVersion")
        else:
            # sponge2 (ithink)
            version = root.get("Version")
            data_version = root.get("DataVersion")
        
        if version is None or data_version is None:
            
            logging.info(f"NBT structure: {root}")
            await interaction.response.send_message("missing nbt tags (Version/dataversion)", ephemeral=True)
            return
        
        minecraft_version = map_data_version(data_version)
        schematic_format = get_schematic_format(version)
        
        worldeditcommand = f"//schem load {file.filename}"
        if schematic_format == "schem.2":
            worldeditcommand = f"//schem load {file.filename} sponge.2"
        elif schematic_format == "schem.3":
            worldeditcommand = f"//schem load {file.filename} sponge.3"
        

        if interaction.guild_id == 256198526248157186:
            # For BR schematic center
            embed = discord.Embed(
                title=f"Schematic: {file.filename}",
                description=(
                    f"**__Format:__**"
                    f"\n> {schematic_format}"
                    f"\n**__MC version:__**"
                    f"\n> {minecraft_version}"
                    f"\n\n# loading with Axiom"
                    f"\n- `file > import schematic`"
                    f"\n - choose `{file.filename}`"
                    f"\n\n# loading with Worledit"
                    f"\n- Put `{file.filename}` into your `.minecraft\config\worldedit\schematics` folder"
                    f"\n - ```{worldeditcommand}```"
                    f"\n\n# loading with FAWE"
                    f"\n- Upload {file.filename} to [**FAWE schematic center**](<https://schem.intellectualsites.com/fawe/index.php>) (or [**BR schematic center**](<https://www.buildersrefuge.com/schematics/>))"
                    f"\n-# Use BR schem center if uploading to BR"
                    f"\n - Change outputted command do `//schematic load {schematic_format} url:URLHERE`"
                    f"\n - Paste command in game"
                ),
                colour=0xFF5733,
            )

        else:
            embed = discord.Embed(
                title=file.filename,
                description=(
                    f"**__Format:__**"
                    f"\n> {schematic_format}"
                    f"\n**__MC version:__**"
                    f"\n> {minecraft_version}"
                    f"\n\n# loading with Axiom"
                    f"\n- `file > import schematic`"
                    f"\n - choose `{file.filename}`"
                    f"\n\n# loading with Worledit"
                    f"\n- Put `{file.filename}` into your `.minecraft\config\worldedit\schematics` folder"
                    f"\n - ```{worldeditcommand}```"
                    f"\n\n# loading with FAWE"
                    f"\n- Upload {file.filename} to [**FAWE schematic center**](<https://schem.intellectualsites.com/fawe/index.php>)"
                    f"\n - Change outputted command do `//schematic load {schematic_format} url:URLHERE`"
                    f"\n - Paste command in game"
                ),
                colour=0x1a6b52,
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        logging.info(f"output sent to {interaction.user}")
    except Exception as e:
        await interaction.response.send_message(f"error in file: {e}", ephemeral=True)

bot.run(secret.token)
