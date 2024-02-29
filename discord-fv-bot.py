import discord
from discord.ext import commands
import sqlite3
from tabulate import tabulate
import datetime
from discord import FFmpegPCMAudio, PCMVolumeTransformer
import pafy
import urllib.request
import re
import yt_dlp as youtube_dl  


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}

# Conexión a la base de datos SQLite
conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS jugadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        numero INTEGER,
        apodo TEXT,
        goles INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS partidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        hora TEXT,
        rival TEXT,
        resultado TEXT,
        direccion_cancha TEXT,
        jugadores_convocados TEXT
    )
''')

@bot.event
async def on_ready():
    print(f'{bot.user.name} conectado')

@bot.command()
async def nuevojugador(ctx):
    await ctx.send("Por favor, ingresa el nombre:")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    nombre = response.content

    await ctx.send("Por favor, ingresa el número:")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    numero = response.content

    # Verificar si el número de jugador ya existe en la base de datos
    cursor.execute('SELECT nombre, numero, apodo, goles FROM jugadores WHERE numero = ?', (numero,))
    resultado = cursor.fetchone()

    if resultado is not None:
        await ctx.send('Ya existe un jugador con ese número.')
        return

    await ctx.send("Por favor, ingresa el apodo:")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    apodo = response.content

    await ctx.send("Por favor, ingresa la cantidad de goles:")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    goles = int(response.content)

    # Insertar la información del jugador en la tabla sin especificar el ID
    cursor.execute('INSERT INTO jugadores (nombre, numero, apodo, goles) VALUES (?, ?, ?, ?)', (nombre, numero, apodo, goles))
    conn.commit()
    await ctx.send('Información guardada correctamente.')

@bot.command()
async def mostrarjugadores(ctx):
    await ctx.send("Por favor, ingresa el número del jugador o escribe 'todos' para mostrar todos los jugadores:")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    numero_jugador = response.content

    try:
        if numero_jugador.lower() == 'todos':
            # Obtener la información de todos los jugadores desde la tabla, ordenados por goles en orden descendente
            cursor.execute('SELECT nombre, numero, goles FROM jugadores ORDER BY goles DESC')
            resultados = cursor.fetchall()

            if resultados:
                headers = ["Nombre", "Número", "Goles"]
                rows = []
                for resultado in resultados:
                    nombre, numero, goles = resultado
                    rows.append([nombre, numero, goles])
                table = tabulate(rows, headers=headers, tablefmt="orgtbl")
                await ctx.send(f'Información de todos los jugadores ordenados por goles:\n```\n{table}\n```')
            else:
                await ctx.send('No se encontraron jugadores registrados.')
        else:
            # Obtener la información del jugador específico desde la tabla
            cursor.execute('SELECT nombre, numero, apodo, goles FROM jugadores WHERE numero = ?', (numero_jugador,))
            resultado = cursor.fetchone()

            if resultado is not None:
                nombre, numero, apodo, goles = resultado

                embed = discord.Embed(title="Información del jugador", color=discord.Color.dark_gray())
                embed.add_field(name="Nombre", value=nombre, inline=False)
                embed.add_field(name="Número", value=numero, inline=False)
                embed.add_field(name="Apodo", value=apodo, inline=False)
                embed.add_field(name="Goles", value=goles, inline=False)

                await ctx.send(embed=embed)
            else:
                await ctx.send('No se encontró un jugador con ese número.')
    except Exception as error:
        print("Error inesperado:", error)

@bot.command()
async def actualizarjugador(ctx):
    await ctx.send("Por favor, ingresa el número del jugador que deseas actualizar:")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    numero_jugador = response.content

    # Verificar si el jugador existe en la base de datos
    cursor.execute('SELECT nombre, numero, goles, apodo FROM jugadores WHERE numero = ?', (numero_jugador,))
    resultado = cursor.fetchone()

    if resultado is not None:
        nombre, numero, goles_actuales, apodo = resultado

        card = discord.Embed(title="Información del Jugador", color=discord.Color.blue())
        card.add_field(name="Nombre", value=nombre, inline=False)
        card.add_field(name="Número", value=numero, inline=False)
        card.add_field(name="Goles actuales", value=goles_actuales, inline=False)
        card.add_field(name="Apodo", value=apodo, inline=False)

        await ctx.send(embed=card)

        await ctx.send("Por favor, ingresa el campo que deseas modificar (nombre, numero, goles, apodo):")
        response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
        campo = response.content.lower()

        if campo == 'nombre':
            await ctx.send("Por favor, ingresa el nuevo nombre:")
            response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            nuevo_nombre = response.content

            # Actualizar el nombre del jugador en la base de datos
            cursor.execute('UPDATE jugadores SET nombre = ? WHERE numero = ?', (nuevo_nombre, numero_jugador))
            conn.commit()

            await ctx.send(f'Nombre actualizado correctamente. Nuevo nombre: {nuevo_nombre}')

        elif campo == 'numero':
            await ctx.send("Por favor, ingresa el nuevo número:")
            response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            nuevo_numero = response.content

            # Verificar si el nuevo número de jugador ya existe en la base de datos
            cursor.execute('SELECT nombre, numero, goles, apodo FROM jugadores WHERE numero = ?', (nuevo_numero,))
            resultado = cursor.fetchone()

            if resultado is not None:
                await ctx.send('Ya existe un jugador con ese número.')
                return

            # Actualizar el número del jugador en la base de datos
            cursor.execute('UPDATE jugadores SET numero = ? WHERE numero = ?', (nuevo_numero, numero_jugador))
            conn.commit()

            await ctx.send(f'Número actualizado correctamente. Nuevo número: {nuevo_numero}')

        elif campo == 'goles':
            await ctx.send("Por favor, ingresa la cantidad de goles a sumar:")
            response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            goles_a_sumar = int(response.content)

            nuevos_goles = goles_actuales + goles_a_sumar

            # Actualizar los goles del jugador en la base de datos
            cursor.execute('UPDATE jugadores SET goles = ? WHERE numero = ?', (nuevos_goles, numero_jugador))
            conn.commit()

            await ctx.send(f'Goles actualizados correctamente. Nuevos goles: {nuevos_goles}')

        elif campo == 'apodo':
            await ctx.send("Por favor, ingresa el nuevo apodo:")
            response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
            nuevo_apodo = response.content

            # Actualizar el apodo del jugador en la base de datos
            cursor.execute('UPDATE jugadores SET apodo = ? WHERE numero = ?', (nuevo_apodo, numero_jugador))
            conn.commit()

            await ctx.send(f'Apodo actualizado correctamente. Nuevo apodo: {nuevo_apodo}')

        else:
            await ctx.send('Campo no válido. No se realizaron modificaciones.')

    else:
        await ctx.send('No se encontró un jugador con ese número.')

@bot.command()
async def borrarjugador(ctx):
    await ctx.send("Por favor, ingresa el número del jugador que deseas borrar:")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    numero_jugador = response.content

    # Verificar si el jugador existe en la base de datos
    cursor.execute('SELECT nombre, numero, goles, apodo FROM jugadores WHERE numero = ?', (numero_jugador,))
    resultado = cursor.fetchone()

    if resultado is not None:
        nombre, numero, goles, apodo = resultado

        card = discord.Embed(title="Información del Jugador", color=discord.Color.red())
        card.add_field(name="Nombre", value=nombre, inline=False)
        card.add_field(name="Número", value=numero, inline=False)
        card.add_field(name="Goles", value=goles, inline=False)
        card.add_field(name="Apodo", value=apodo, inline=False)

        await ctx.send(embed=card)

        # Preguntar al usuario si está seguro de borrar al jugador
        await ctx.send("¿Estás seguro de que deseas borrar a este jugador? Responde `si` o `no`.")

        def check_confirmation(message):
            return message.author == ctx.author and message.content.lower() in ['si', 'no']

        confirmation = await bot.wait_for('message', check=check_confirmation)

        if confirmation.content.lower() == 'si':
            # Eliminar el jugador de la base de datos
            cursor.execute('DELETE FROM jugadores WHERE numero = ?', (numero_jugador,))
            conn.commit()

            await ctx.send('Jugador eliminado correctamente.')
        else:
            await ctx.send('Operación cancelada. El jugador no ha sido eliminado.')
    else:
        await ctx.send('No se encontró un jugador con ese número.')

@bot.command()
async def nuevopartido(ctx):
    await ctx.send("Por favor, ingresa la fecha del partido (formato DD/MM):")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    fecha = response.content

    await ctx.send("Por favor, ingresa la hora del partido (formato XX:XXhs):")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    hora = response.content

    await ctx.send("Por favor, ingresa el nombre del rival:")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    rival = response.content

    await ctx.send("Por favor, ingresa la dirección de la cancha:")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    direccion_cancha = response.content

    await ctx.send("Por favor, ingresa los jugadores convocados (separados por coma):")
    response = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    jugadores_convocados = response.content

    # Insertar el partido en la tabla "partidos"
    cursor.execute('''
        INSERT INTO partidos (fecha, hora, rival, direccion_cancha, jugadores_convocados)
        VALUES (?, ?, ?, ?, ?)
    ''', (fecha, hora, rival, direccion_cancha, jugadores_convocados))
    conn.commit()

    await ctx.send('Partido guardado correctamente.')

@bot.command()
async def mostrarpartidos(ctx):
    # Obtener los próximos partidos basados en la fecha actual y la cantidad ingresada
    cursor.execute('SELECT id, fecha, hora, rival, resultado, direccion_cancha, jugadores_convocados FROM partidos ORDER BY fecha ASC')
    resultados = cursor.fetchall()

    try:
        if resultados:
            for result in resultados:
                numero_partido, fecha, hora, rival, resultado, direccion_cancha, jugadores_convocados = result
                # Construir la tarjeta de información del partido
                if resultado == 'v':
                    color = discord.Color.green()
                    resultado = 'Victoria'
                elif resultado == 'd':
                    color = discord.Color.red()
                    resultado = 'Derrota'
                else:
                    color = discord.Color.blue()
                try:
                    fecha_objeto = datetime.datetime.strptime(fecha, "%Y-%m-%d")
                    fecha_transformada = fecha_objeto.strftime("%d/%m")
                except:
                    fecha_transformada = fecha
                card = discord.Embed(title=f"Partido #{numero_partido}", color=color)
                card.add_field(name="Fecha", value=fecha_transformada, inline=False)
                card.add_field(name="Hora", value=hora, inline=False)
                card.add_field(name="Rival", value=rival, inline=False)
                if resultado != None:
                    card.add_field(name="Resultado", value=resultado, inline=False)
                card.add_field(name="Dirección de la cancha", value=direccion_cancha, inline=False)
                card.add_field(name= "{:<20}".format('Jugadores convocados'), value=jugadores_convocados, inline=False)

                await ctx.send(embed=card)
        else:
            await ctx.send('No hay próximos partidos programados.')
    except Exception as error:
        print("Error inesperado:", error)

@bot.command()
async def proximopartido(ctx):
    # Obtener la fecha actual
    fecha_actual = datetime.date.today().strftime("%d/%m")

    # Obtener los próximos partidos basados en la fecha actual y la cantidad ingresada
    cursor.execute('SELECT id, fecha, hora, rival, direccion_cancha, jugadores_convocados FROM partidos WHERE fecha >= ? ORDER BY fecha DESC LIMIT 1', (fecha_actual,))
    resultados = cursor.fetchall()

    try:
        if resultados:
            for resultado in resultados:
                numero_partido, fecha, hora, rival, direccion_cancha, jugadores_convocados = resultado
                # Construir la tarjeta de información del partido
                try:
                    fecha_objeto = datetime.datetime.strptime(fecha, "%Y-%m-%d")
                    fecha_transformada = fecha_objeto.strftime("%d/%m")
                except:
                    fecha_transformada = fecha
                card = discord.Embed(title=f"Partido #{numero_partido}", color=discord.Color.blue())
                card.add_field(name="Fecha", value=fecha_transformada, inline=False)
                card.add_field(name="Hora", value=hora, inline=False)
                card.add_field(name="Rival", value=rival, inline=False)
                card.add_field(name="Dirección de la cancha", value=direccion_cancha, inline=False)
                card.add_field(name="{:<20}".format('Jugadores convocados'), value=jugadores_convocados, inline=False)

                await ctx.send(embed=card)
        else:
            await ctx.send('No hay próximos partidos programados.')
    except Exception as error:
        print("Error inesperado:", error)

@bot.command()
async def mostrarpartidosviejos(ctx):
    # Obtener la fecha actual
    fecha_actual = datetime.date.today().strftime("%d/%m")

    # Obtener los próximos partidos basados en la fecha actual y la cantidad ingresada
    cursor.execute('SELECT id, fecha, hora, rival, resultado, direccion_cancha, jugadores_convocados FROM partidos WHERE fecha < ? ORDER BY fecha DESC', (fecha_actual,))
    resultados = cursor.fetchall()
    if resultados:
        for result in resultados:
            numero_partido, fecha, hora, rival, resultado, direccion_cancha, jugadores_convocados = result
            # Construir la tarjeta de información del partido
            if resultado == 'v':
                color = discord.Color.green()
                resultado = 'Victoria'
            elif resultado == 'd':
                color = discord.Color.red()
                resultado = 'Derrota'
            else:
                color = discord.Color.blue()
      
            card = discord.Embed(title=f"Partido #{numero_partido}", color=color)
            card.add_field(name="Fecha", value=fecha, inline=False)
            card.add_field(name="Hora", value=hora, inline=False)
            card.add_field(name="Rival", value=rival, inline=False)
            card.add_field(name="Resultado", value=resultado, inline=False)
            card.add_field(name="Dirección de la cancha", value=direccion_cancha, inline=False)
            card.add_field(name="{:<20}".format('Jugadores convocados'), value=jugadores_convocados, inline=False)

            await ctx.send(embed=card)
    else:
        await ctx.send('No hay partidos anteriores.')

# @bot.command()
# async def borrarpartido(ctx):
#     await ctx.send("Ingresa la fecha del partido a eliminar (DD/MM):")

#     message = await bot.wait_for("message", timeout=30, check=lambda message: message.author == ctx.author)
#     fecha = message.content
#     cursor.execute('SELECT * FROM partidos WHERE fecha = ?', (fecha,))
#     resultado = cursor.fetchone()
#     if resultado is not None:
#         cursor.execute('DELETE FROM partidos WHERE fecha = ?', (fecha,))
#         conn.commit()
#         await ctx.send(f"Se ha eliminado el partido del {fecha}.")
#     else:
#         await ctx.send(f"No se encontró un partido programado para el {fecha}.")

@bot.command()
async def editarpartido(ctx):
    await ctx.send("Ingresa la fecha del partido que deseas editar (DD/MM):")

    def check(message):
        return message.author == ctx.author

    try:
        message = await bot.wait_for("message", timeout=30, check=check)
        fecha_str = message.content

        cursor.execute('SELECT * FROM partidos WHERE fecha = ?', (fecha_str,))
        resultado = cursor.fetchone()

        if resultado is not None:
            numero_partido, fecha, hora, rival, direccion, convocados, resultado = resultado

            await ctx.send(f"Editando el Partido #{numero_partido}.")
            await ctx.send("¿Qué campo deseas modificar? Puedes elegir entre: fecha, hora, rival, resultado, direccion, convocados")

            message = await bot.wait_for("message", timeout=30, check=check)
            campo = message.content.lower()

            if campo == "fecha":
                await ctx.send("Ingresa la nueva fecha del partido (DD/MM):")
                message = await bot.wait_for("message", timeout=30, check=check)
                nueva_fecha_str = message.content

                cursor.execute('UPDATE partidos SET fecha = ? WHERE id = ?', (nueva_fecha_str, numero_partido))
                conn.commit()
                await ctx.send(f"Se ha actualizado la fecha del Partido #{numero_partido}.")

            elif campo == "hora":
                await ctx.send("Ingresa la nueva hora del partido (formato XX:XXhs):")
                message = await bot.wait_for("message", timeout=30, check=check)
                nueva_hora = message.content

                cursor.execute('UPDATE partidos SET hora = ? WHERE id = ?', (nueva_hora, numero_partido))
                conn.commit()
                await ctx.send(f"Se ha actualizado la hora del Partido #{numero_partido}.")

            elif campo == "rival":
                await ctx.send("Ingresa el nuevo rival:")
                message = await bot.wait_for("message", timeout=30, check=check)
                nuevo_rival = message.content

                cursor.execute('UPDATE partidos SET rival = ? WHERE id = ?', (nuevo_rival, numero_partido))
                conn.commit()
                await ctx.send(f"Se ha actualizado el rival del Partido #{numero_partido}.")

            elif campo == "resultado":
                await ctx.send("Ingresa el nuevo resultado (v / d):")
                message = await bot.wait_for("message", timeout=30, check=check)
                nuevo_resultado = message.content

                cursor.execute('UPDATE partidos SET resultado = ? WHERE id = ?', (nuevo_resultado, numero_partido))
                conn.commit()
                await ctx.send(f"Se ha actualizado el resultado del Partido #{numero_partido}.")

            elif campo == "direccion":
                await ctx.send("Ingresa la nueva dirección de la cancha:")
                message = await bot.wait_for("message", timeout=30, check=check)
                nueva_direccion = message.content

                cursor.execute('UPDATE partidos SET direccion_cancha = ? WHERE id = ?', (nueva_direccion, numero_partido))
                conn.commit()
                await ctx.send(f"Se ha actualizado la dirección de la cancha del Partido #{numero_partido}.")

            elif campo == "convocados":
                await ctx.send("Ingresa los nuevos jugadores convocados (separados por coma):")
                message = await bot.wait_for("message", timeout=30, check=check)
                nuevos_convocados = message.content

                cursor.execute('UPDATE partidos SET jugadores_convocados = ? WHERE id = ?', (nuevos_convocados, numero_partido))
                conn.commit()
                await ctx.send(f"Se ha actualizado los jugadores convocados del Partido #{numero_partido}.")

            else:
                await ctx.send("Campo no válido. Por favor, intenta nuevamente.")

        else:
            await ctx.send("No se encontró un partido con la fecha ingresada.")

    except Exception as error:
        print("Error inesperado:", error)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("El comando no existe. Por favor, intenta con otro comando. Usa `!ayuda` para obtener una lista de comandos disponibles.")

@bot.command()
async def reproducir(ctx, url):
    # Verificar si el bot ya se encuentra en un canal de voz
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(voice_channel)
    else:
        voice_client = await voice_channel.connect()

    # Descargar y reproducir el audio desde la URL

    song = pafy.new(url)  # creates a new pafy object using the provided URL

    audio = song.getbestaudio()  # gets an audio source

    source = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)  # converts the YouTube audio source into a source Discord can use

    voice_client.play(source)  # play the source

async def detener(ctx):
    # Verificar si el bot está en un canal de voz
    if ctx.voice_client is None:
        await ctx.send("No estoy conectado a un canal de voz.")
        return

    # Detener la reproducción de música
    ctx.voice_client.stop()

    # Desconectar al bot del canal de voz
    await ctx.voice_client.disconnect()
    await ctx.send("Me he desconectado del canal de voz.")

@bot.command()
async def ayuda(ctx):
    # Crear una lista de comandos con descripciones
    commands_list = [
        {"name": "nuevojugador", "description": "Guardar información de un jugador."},
        {"name": "mostrarjugadores", "description": "Mostrar información de un jugador o todos los jugadores."},
        {"name": "actualizarjugador", "description": "Actualizar la cantidad de goles de un jugador."},
        {"name": "borrarjugador", "description": "Borrar a un jugador."},
        {"name": "nuevopartido", "description": "Agregar un partido nuevo a la agenda."},
        {"name": "proximopartido", "description": "Mostrar el próximo partido en la agenda."},
        {"name": "mostrarpartidos", "description": "Mostrar todos los partidos en la agenda."},
        {"name": "mostrarpartidosviejos", "description": "Mostrar todos los partidos ya jugados en la agenda."},
        #{"name": "borrarpartido", "description": "Borrar un partido en la agenda."},
        {"name": "editarpartido", "description": "Editar un partido en la agenda."},
        {"name": "reproducir", "description": "Reproducir musica con un link."},
        {"name": "detener", "description": "Parar la reproduccion."},
    ]

    # Crear una tarjeta Embed
    embed = discord.Embed(title="Lista de comandos disponibles", color=discord.Color.gold())

    # Agregar cada comando y descripción a la tarjeta Embed
    for command in commands_list:
        embed.add_field(name=f"!{command['name']}", value=command['description'], inline=False)

    # Enviar la tarjeta Embed como respuesta
    await ctx.send(embed=embed)

    

bot.run('')
