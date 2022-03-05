from telethon import Button
from bot import SessionVars
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified
from ..core.get_vars import get_val
import subprocess
import asyncio
import re
import logging
from .progress_for_rclone import status

log = logging.getLogger(__name__)

async def rclone_copy_transfer(e, conf_path):

    origin_drive = get_val("ORIGIN_DRIVE")
    origin_dir = get_val("ORIGIN_DIR")
    dest_drive = get_val("DEST_DRIVE")
    dest_dir = get_val("DEST_DIR")

    log.info(f'{origin_drive}:{origin_dir}-{dest_drive}:{dest_dir}')

    rclone_copy_cmd = ['rclone', 'copy', f'--config={conf_path}', f'{origin_drive}:{origin_dir}',
                       f'{dest_drive}:{dest_dir}', '-P']

    message = await e.edit("Preparing to copy...")

    rclone_pr = subprocess.Popen(
        rclone_copy_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    rcres = await rclone_process_update(rclone_pr, message)

    if rcres:
        rclone_pr.kill()
        await message.edit("Copy cancelled")
        return

    await message.edit("Successfully ✅")


async def rclone_process_update(rclone_pr, message):
    blank = 0
    process = rclone_pr
    user_message = message
    sleeps = False
    msg = ""
    msg1 = ""

    while True:
        data = process.stdout.readline().decode().strip()
        mat = re.findall("Transferred:.*ETA.*", data)

        if mat is not None:
            if len(mat) > 0:
                sleeps = True
                nstr = mat[0].replace("Transferred:", "")
                nstr = nstr.strip()
                nstr = nstr.split(",")
                log.info(nstr[1])
                percent = nstr[1].strip("% ")
                try:
                    percent = int(percent)
                except:
                    percent = 0
                prg = status(percent)

                msg = 'Copying...\n{} \n{} \nSpeed:- {} \nETA:- {}\n'.format(nstr[0], prg, nstr[2],
                                                                                    nstr[3].replace("ETA", ""))

                keyboard = [[Button.inline("Cancel", "upcancel")]]

                if msg1 != msg:
                     try:
                        await user_message.edit(text=msg, buttons=keyboard)
                        msg1= msg
                     except MessageNotModified: 
                        pass    

        if data == "":
            blank += 1
            if blank == 20:
                log.info("blank reached 20")
                break
        else:
            blank = 0

        if sleeps:
            sleeps = False
            if get_val("UPLOAD_CANCEL"):
                SessionVars.update_var("UPLOAD_CANCEL", False)
                return True
            await asyncio.sleep(2)
            process.stdout.flush()
