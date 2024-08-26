# Bot de turnos para la VTV de CABA

Podés escribirle al bot directamente en telegram, [Turnos VTV CABA](https://t.me/turnos_cabavtv_bot), o levantar el tuyo y configurarlo. El bot te muestra que días hay turnos disponibles dependiendo de la planta que hayas elegido, o que te notifique cuando aparezcan turnos en tu planta favorita.

## Levantar tu propio bot
1. Hablale a `@BotFather` y creá un nuevo bot, copiate el token.
2. El token ponelo en la env var `TELEGRAM_BOT_API_KEY`.
3. Levantá todo con `docker compose up`.