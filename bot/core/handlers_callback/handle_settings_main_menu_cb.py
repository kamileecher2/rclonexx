import logging
from bot.core.get_vars import get_val
from bot.core.settings_main_menu import general_input_manager, get_value, settings_main_menu
from bot.core.set_vars import set_val

torlog = logging.getLogger(__name__)

async def handle_setting_main_menu_callback(callback_query):
    data = callback_query.data.decode()
    cmd = data.split("^")
    mmes = await callback_query.get_message()
    val = ""
    base_dir= get_val("BASE_DIR")
    rclone_drive = get_val("DEF_RCLONE_DRIVE")

    if callback_query.data == "pages":
        await callback_query.answer()

    if cmd[1] == "load_rclone_config":
        await callback_query.answer("Send rclone.conf file", alert=True)
        await mmes.edit(f"Send rclone.conf file\n\n/ignore to go back", buttons=None)
        val = await get_value(callback_query, True)

        await general_input_manager(callback_query, mmes, "RCLONE_CONFIG", "str", val, "rclonemenu")

    elif cmd[1] == "list_drive_main_menu":
        set_val("BASE_DIR", "")
        base_dir = get_val("BASE_DIR")
        set_val("DEF_RCLONE_DRIVE", cmd[2])
        await settings_main_menu(
            callback_query, 
            mmes, 
            edit=True,
            msg=f"Select folder where you want to store files\n\nPath:`{cmd[2]}:{base_dir}`", 
            drive_name= cmd[2], 
            submenu="list_drive", 
            data_cb="list_dir_main_menu", 
            )     

    elif cmd[1] == "list_dir_main_menu":
        rclone_drive = get_val("DEF_RCLONE_DRIVE")
        rclone_dir= get_val("BASE_DIR")
        path = get_val(cmd[2])
        logging.info("path: {}".format(path))
        rclone_dir +=  path +"/"
        set_val("BASE_DIR", rclone_dir)
        await settings_main_menu(
            callback_query, mmes, 
            edit=True, 
            msg=f"Select folder where you want to store files\n\nPath:`{rclone_drive}:{rclone_dir}`", 
            drive_base=rclone_dir, 
            drive_name= rclone_drive, 
            submenu="list_drive", 
            data_cb="list_dir_main_menu", 
            )

    # close menu
    elif cmd[1] == "selfdest":
        await callback_query.answer("Closed")
        await callback_query.delete()