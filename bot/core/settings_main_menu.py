from bot.core.set_vars import set_val
from telethon.tl.types import KeyboardButtonCallback
from telethon import events
from bot import SessionVars
from bot.utils.list_selected_drive_main_menu import list_selected_drive
from .get_vars import get_val
from functools import partial
import asyncio
import time, os, configparser, logging, traceback

torlog = logging.getLogger(__name__)

TIMEOUT_SEC = 60

no = "❌"
yes = "✅"
drive_icon= "☁️"
header = ""


async def settings_main_menu(
    query, mmes="", 
    drive_base="", 
    edit=False, 
    msg="", 
    drive_name="", 
    data_cb="", 
    submenu=None, 
    session_id=None, 
    is_dest_drive= False
    ):
    menu = []

    if submenu is None:
        rcval = await get_string_variable("RCLONE_CONFIG", menu, "load_rclone_config")

        if rcval != "None":
            if "Rclone config file loaded" in rcval:
                path= os.path.join(os.getcwd(), "rclone.conf")
                conf = configparser.ConfigParser()
                conf.read(path)

                def_drive = get_val("DEF_RCLONE_DRIVE")

                for j in conf.sections():
                    prev = ""
                    if j == def_drive:
                        prev = yes

                    if "team_drive" in list(conf[j]):
                        menu.append(
                            [KeyboardButtonCallback(f"{prev}{j} - TD", f"mainmenu^list_drive_main_menu^{j}")]   
                        )
                    else:
                        menu.append(
                            [KeyboardButtonCallback(f"{prev}{j} - ND", f"mainmenu^list_drive_main_menu^{j}")]
                        )
        menu.append(
            [KeyboardButtonCallback("Close Menu", f"mainmenu^selfdest")]
        )
        base_dir= get_val("BASE_DIR")
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        msg= f"Select cloud where you want to upload file\n\nPath:`{rclone_drive}:{base_dir}`"

        await query.reply(header + msg, parse_mode="md", buttons=menu, link_preview=False)


    elif submenu == "list_drive":
        conf_path = await get_config()

        await list_selected_drive(
            query, 
            drive_base, 
            drive_name, 
            conf_path, 
            data_cb, 
            menu, 
            )

        menu.append(
            [KeyboardButtonCallback("Close Menu", f"mainmenu^selfdest")]

        )
        if edit:
            await mmes.edit(msg,
                                 parse_mode="md", buttons=menu, link_preview=False)
        else:
            await query.reply(header,
                                  parse_mode="md", buttons=menu, link_preview=False)

#####################################                                  

async def general_input_manager(callback_query, mmes, var_name, datatype, value, sub_menu):
    if value is not None and not "ignore" in value:
        await confirm_buttons(mmes, value)
        conf = await get_confirm(callback_query)
        if conf is not None:
            if conf:
                try:
                    if datatype == "int":
                        value = int(value)
                    if datatype == "str":
                        value = str(value)
                    if datatype == "bool":
                        if value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                        else:
                            raise ValueError("Invalid value from bool")

                    if var_name == "RCLONE_CONFIG":
                        try:
                            conf = configparser.ConfigParser()
                            conf.read(value)

                            for i in conf.sections():
                                SessionVars.update_var("DEF_RCLONE_DRIVE", str(i))
                                break

                            SessionVars.update_var("RCLONE_CONFIG", os.path.join(os.getcwd(), value))

                        except Exception:
                            torlog.error(traceback.format_exc())
                            await handle_settings_main_menu(mmes, True, f"<b><u>The conf file is invalid check logs.</b></u>",
                                                  sub_menu)
                            return

                    else:
                        SessionVars.update_var(var_name, value)

                    await handle_settings_main_menu(mmes, True,
                                          f"<b><u>Recibido {var_name} valor '{value}'.</b></u>", sub_menu)
                except ValueError:
                    await handle_settings_main_menu(mmes, True,
                                          f"<b><u>Value [{value}] not valid try again and enter {datatype}.</b></u>",
                                          sub_menu)
            else:
                await handle_settings_main_menu(mmes, True, f"<b><u>Confirm differed by user.</b></u>", sub_menu)
        else:
            await handle_settings_main_menu(mmes, True, f"<b><u>Confirm timed out [waited 60s for input].</b></u>", sub_menu)
    else:
        await handle_settings_main_menu(mmes, True, f"<b><u>Entry Timed out [waited 60s for input]. OR else ignored.</b></u>",
                              sub_menu)


async def get_value(callback_query, file=False):
    lis = [False, None]

    cbak = partial(val_input_callback, o_sender=callback_query.sender_id, lis=lis, file=file)

    callback_query.client.add_event_handler(
        cbak,
        events.NewMessage()
    )

    start = time.time()

    while not lis[0]:
        if (time.time() - start) >= TIMEOUT_SEC:
            break

        await asyncio.sleep(1)

    val = lis[1]

    callback_query.client.remove_event_handler(cbak)

    return val


async def get_confirm(callback_query):
    lis = [False, None]
    cbak = partial(get_confirm_callback, o_sender=callback_query.sender_id, lis=lis)

    callback_query.client.add_event_handler(
        cbak,
        events.CallbackQuery(pattern="confirmsetting")
    )

    start = time.time()

    while not lis[0]:
        if (time.time() - start) >= TIMEOUT_SEC:
            break
        await asyncio.sleep(1)

    val = lis[1]

    callback_query.client.remove_event_handler(cbak)

    return val


async def val_input_callback(callback_query, o_sender, lis, file):
    if o_sender != callback_query.sender_id:
        return
    if not file:
        lis[0] = True
        lis[1] = callback_query.text
        await callback_query.delete()
    else:
        if callback_query.document is not None:
            path = await callback_query.download_media()
            lis[0] = True
            lis[1] = path
            await callback_query.delete()
        else:
            if "ignore" in callback_query.text:
                lis[0] = True
                lis[1] = "ignore"
                await callback_query.delete()
            else:
                await callback_query.delete()

    raise events.StopPropagation


async def get_confirm_callback(callback_query, o_sender, lis):
    if o_sender != callback_query.sender_id:
        return
    lis[0] = True

    data = callback_query.data.decode().split(" ")
    if data[1] == "true":
        lis[1] = True
    else:
        lis[1] = False


async def confirm_buttons(callback_query, val):
    await callback_query.edit(f"Confirmar lo enviado :- <u>{val}</u>", buttons=[KeyboardButtonCallback("Yes", "confirmsetting true"),
                                                                KeyboardButtonCallback("No", "confirmsetting false")],
                 parse_mode="html")


async def get_bool_variable(var_name, msg, menu, callback_name, session_id):
    val = get_val(var_name)

    if val:
        menu.append(
            [KeyboardButtonCallback(yes + msg, f"copymenu^{callback_name}^false^{session_id}")]
        )
    else:
        menu.append(
            [KeyboardButtonCallback(no + msg, f"copymenu^{callback_name}^true^{session_id}")]
        )


async def get_sub_menu(msg, sub_name, menu):
    menu.append(
        [KeyboardButtonCallback(msg, f"mainmenu^{sub_name}")]
    )


async def get_string_variable(var_name, menu, callback_name):
    if var_name == "RCLONE_CONFIG":
        rfile= os.path.join(os.getcwd(), "rclone.conf")
        if os.path.exists(rfile):
           val = "Rclone config file loaded (Click to load another)"
        else:
           val = "Click here to load a rclone config file."
    msg = str(val)
    menu.append(
        [KeyboardButtonCallback(msg, f"mainmenu^{callback_name}")]
    )

    return val


async def get_int_variable(var_name, menu, callback_name, session_id):
    val = get_val(var_name)
    msg = var_name + " " + str(val)
    menu.append(
        [KeyboardButtonCallback(msg, f"mainmenu^{callback_name}")]
    )

async def get_config():
    config = os.path.join(os.getcwd(), "rclone.conf")
    if isinstance(config, str):
        if os.path.exists(config):
            return config

    return None
